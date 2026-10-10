"""Conservative model curation using stored visible scores, never query-only scores.

The database's raw accuracy ranking remains the audit source. Missing, inconsistent,
or incomparable metadata cannot turn a model into a compact incumbent.
"""

from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path

from .benchmark import PRIMARY_METRIC, SELECTION_RULES

POLICY_VERSION = "visible_compact_v1"
PROTOCOL_FIELDS = ("selection_rule", "cv_folds", "cv_seed", "n_visible", "n_validation")


def enabled(cfg: dict) -> bool:
    return (cfg.get("curation") or {}).get("enabled") is True


def score_tolerance(cfg: dict) -> float:
    value = (cfg.get("curation") or {}).get("score_tolerance", 0.0)
    if isinstance(value, bool):
        raise ValueError("curation.score_tolerance must be finite and nonnegative")
    try:
        tolerance = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("curation.score_tolerance must be finite and nonnegative") from exc
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError("curation.score_tolerance must be finite and nonnegative")
    return tolerance


def _finite(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _integer(value, minimum=0) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= minimum


@lru_cache(maxsize=4096)
def _artifact_metadata(path: str, inode: int, size: int, mtime_ns: int) -> dict:
    """Cache only small metadata, keyed by immutable file identity and revision."""
    try:
        data = json.loads(Path(path).read_text())
        if not isinstance(data, dict):
            return {}
        out = {k: data[k] for k in ("n_features", *PROTOCOL_FIELDS) if k in data}
        if isinstance(data.get("columns"), list):
            out["column_count"] = len(data["columns"])
        return out
    except (OSError, ValueError, TypeError):
        return {}


def artifact_metadata(record: dict) -> dict:
    if not record.get("artifact_dir"):
        return {}
    try:
        path = Path(record["artifact_dir"]) / "result.json"
        st = path.stat()
    except (OSError, TypeError):
        return {}
    return _artifact_metadata(str(path.resolve()), st.st_ino, st.st_size, st.st_mtime_ns)


def _agreed(field: str, sources: list[dict]):
    values = [s[field] for s in sources if field in s]
    if not values:
        raise ValueError(f"missing {field}")
    first = values[0]
    if any(type(v) is not type(first) or v != first for v in values[1:]):
        raise ValueError(f"conflicting {field}")
    return first


def visible_metadata(record: dict) -> dict:
    """Validate an allowlisted visible scoring protocol and actual numeric column count."""
    if record.get("status") != "completed" or record.get("kind") == "ensemble":
        raise ValueError("not a completed single model")
    metrics = record.get("val_metrics_json") or {}
    diagnostics = record.get("diagnostics_json") or {}
    hp = record.get("hyperparameters_json") or {}
    if any(not isinstance(s, dict) for s in (metrics, diagnostics, hp)):
        raise ValueError("visible metadata must be JSON objects")
    # Diagnostics are the normal path. Read an artifact only for missing counts/protocol.
    sources = [metrics, diagnostics, hp]
    if any(not any(k in s for s in sources) for k in ("n_features", *PROTOCOL_FIELDS)):
        sources.append(artifact_metadata(record))
    n_features = _agreed("n_features", sources)
    if not _integer(n_features, 1):
        raise ValueError("n_features must count positive numeric predictor columns")
    for source in sources:
        if "column_count" in source and source["column_count"] != n_features:
            raise ValueError("artifact column count conflicts with n_features")
    protocol = {k: _agreed(k, sources) for k in PROTOCOL_FIELDS}
    for k in ("dataset", "split_id"):
        if not isinstance(record.get(k), str) or not record[k]:
            raise ValueError(f"missing {k}")
        protocol[k] = record[k]
    rule = protocol["selection_rule"]
    if not isinstance(rule, str) or rule not in SELECTION_RULES:
        raise ValueError("unknown selection_rule")
    for k in ("cv_folds", "cv_seed", "n_visible", "n_validation"):
        if not _integer(protocol[k], 1 if k.startswith("n_") else 0):
            raise ValueError(f"invalid {k}")
    cv = protocol["cv_folds"] > 1
    if protocol["cv_folds"] == 1 or (cv and protocol["n_visible"] <= protocol["n_validation"]) or \
            (not cv and protocol["n_visible"] != protocol["n_validation"]):
        raise ValueError("inconsistent visible validation/CV scope")
    # Optional explicit scope tags must also match; never merge public-CV-only and CV+validation.
    for k in ("metric_scope", "selection_protocol"):
        if any(k in s for s in sources):
            protocol[k] = _agreed(k, sources)
            if not isinstance(protocol[k], str) or not protocol[k]:
                raise ValueError(f"invalid {k}")
    expected_scope = "visible_validation_plus_cv" if cv else "visible_validation"
    if "metric_scope" in protocol and protocol["metric_scope"] != expected_scope:
        raise ValueError("metric_scope is not the complete visible selection scope")
    constituents = {}
    for metric in sorted({PRIMARY_METRIC, *SELECTION_RULES[rule]}):
        for key in ([metric, f"{metric}_cv"] if cv else [metric]):
            value = metrics.get(key)
            if not _finite(value):
                raise ValueError(f"missing or nonfinite visible constituent {key}")
            if key.startswith("pearson_") and not -1 <= value <= 1:
                raise ValueError(f"out of range visible constituent {key}")
            constituents[key] = float(value)
    score = record.get("primary_score")
    if not _finite(score):
        raise ValueError("missing or nonfinite visible primary_score")
    if "primary" in metrics and (not _finite(metrics["primary"]) or
                                 not math.isclose(score, metrics["primary"], abs_tol=1e-12, rel_tol=1e-12)):
        raise ValueError("primary_score conflicts with visible metrics")
    nv, n = protocol["n_validation"], protocol["n_visible"]
    expected = sum(weight * (nv * constituents[m] + (n - nv) * constituents.get(f"{m}_cv", 0)) / n
                   for m, weight in SELECTION_RULES[rule].items())
    if not math.isclose(score, expected, rel_tol=1e-10, abs_tol=1e-10):
        raise ValueError("primary_score does not match the visible scoring protocol")
    return {"experiment_id": record["experiment_id"], "visible_score": float(score),
            "n_features": n_features, "protocol": protocol, "constituents": constituents}


def select_compact(records: list[dict], raw_champion: dict | None, cfg: dict) -> dict:
    """Return JSON-safe selection evidence. No query/held-out field is read or copied."""
    tolerance = score_tolerance(cfg)
    raw_id = None if raw_champion is None else raw_champion["experiment_id"]
    result = {"version": POLICY_VERSION, "enabled": True, "score_tolerance": tolerance,
              "raw_accuracy_champion_id": raw_id, "selected_id": raw_id,
              "policy": "Fewest numeric columns above raw visible score minus tolerance; no decrease in any "
                        "visible validation/CV constituent. Same dataset, split and scoring protocol required.",
              "selection_inputs": "stored visible metrics only; query-only metrics excluded",
              "raw_accuracy_champion": None, "compact_selected_winner": None,
              "eligible": [], "pareto_frontier": [], "excluded": [], "fallback_reason": None}
    if raw_champion is None:
        result["fallback_reason"] = "no completed accuracy champion"
        return result
    try:
        raw = visible_metadata(raw_champion)
    except ValueError as exc:
        result["fallback_reason"] = f"raw accuracy champion: {exc}"
        return result
    result["raw_accuracy_champion"] = raw
    valid, eligible = [], []
    by_id = {r["experiment_id"]: r for r in records}
    by_id[raw_id] = raw_champion
    for eid in sorted(by_id):
        record = by_id[eid]
        if record.get("status") != "completed" or record.get("kind") == "ensemble":
            continue
        try:
            meta = visible_metadata(record)
            if meta["protocol"] != raw["protocol"]:
                raise ValueError("visible scoring protocol differs from raw accuracy champion")
            valid.append(meta)
            if meta["visible_score"] < raw["visible_score"] - tolerance:
                raise ValueError("visible primary below accuracy guard")
            if any(meta["constituents"][k] < v for k, v in raw["constituents"].items()):
                raise ValueError("visible validation/CV constituent regressed")
            eligible.append(meta)
        except ValueError as exc:
            result["excluded"].append({"experiment_id": eid, "reason": str(exc)})
    # Score-column frontier is descriptive; guards above decide promotion independently.
    best_at_width = {}
    for meta in valid:
        width = meta["n_features"]
        old = best_at_width.get(width)
        if old is None or (-meta["visible_score"], meta["experiment_id"]) < \
                (-old["visible_score"], old["experiment_id"]):
            best_at_width[width] = meta
    running_best = -math.inf
    for width in sorted(best_at_width):
        meta = best_at_width[width]
        if meta["visible_score"] > running_best:
            result["pareto_frontier"].append(meta)
            running_best = meta["visible_score"]
    eligible.sort(key=lambda m: (m["n_features"], -m["visible_score"], m["experiment_id"]))
    result["eligible"] = eligible
    if eligible:
        selected = eligible[0]
        result["selected_id"] = selected["experiment_id"]
        result["compact_selected_winner"] = selected
    else:
        result["fallback_reason"] = "no candidate passed complete visible metadata and score guards"
    return result


def order_candidates(records: list[dict], selection: dict) -> list[dict]:
    """Frozen chosen model first, raw accuracy audit second, then visible-score order."""
    priority = {eid: i for i, eid in enumerate(dict.fromkeys(
        [selection.get("selected_id"), selection.get("raw_accuracy_champion_id")])) if eid is not None}
    return sorted(records, key=lambda r: (priority.get(r["experiment_id"], 2),
                                         -(r.get("primary_score") or 0), r["experiment_id"]))
