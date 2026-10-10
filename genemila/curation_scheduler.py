"""Bounded deterministic pruning rounds with reserved worker lanes.

The master freezes one completed incumbent's specification per round. These
jobs use the normal guarded experiment path and consume CPU, never LLM calls.
Column screens are learned inside each training fold by the pipeline.
"""

from __future__ import annotations

from copy import deepcopy
import json
import math
import time

from .db import ACTIVE
from .exploit import inherited_feature_params, inherited_hyperparameters
from .features.registry import BUILTIN_FEATURES
from .spec import ALLOWED_MODELS, ExperimentSpec

PROPOSER = "python:curator"
_PENDING = ("queued", *ACTIVE)


def candidates(lab, parent: dict):
    """Column screens and interleaved single/block ablations of one snapshot.

    Blocks contain at most three modules. Dependency-connected blocks are tried
    alongside disjoint pairs: an individually weak module is not globally killed.
    Keeping source dependencies available does not keep their predictor columns.
    """
    features = list(parent.get("feature_set_json") or [])
    model = parent.get("model_type")
    if not features or model not in ALLOWED_MODELS:
        return
    pid = parent["experiment_id"]
    metadata = {item["name"]: item for item in lab.db.features()}
    hp = inherited_hyperparameters(parent)
    default = list(lab.cfg["experiment"]["default_alpha_grid"])
    if model != "ols" and not any(key in hp for key in ("alpha", "alpha_grid")):
        hp["alpha_grid"] = default
    common = dict(kind="config", category="exploit", parent_experiment_id=pid,
                  seed=int(parent.get("seed") or 0), proposer=PROPOSER, priority=0.0)
    screens = ({"method": "variance"},
               {"method": "lasso", "alpha": 0.001, "max_iter": 5000},
               {"method": "elasticnet", "alpha": 0.001, "l1_ratio": 0.5, "max_iter": 5000})
    for screen in screens:
        settings = deepcopy(hp if model == "ridge" else {"alpha_grid": default})
        settings["column_selection"] = screen
        if model == "ridge" and settings == hp:
            continue  # the incumbent already ran this exact screen
        yield ExperimentSpec(
            hypothesis=f"Screen redundant columns with {screen['method']} around frozen incumbent {pid}.",
            scientific_rationale="Learn the column support separately inside each training fold, then test "
                                 "whether a smaller ridge predictor preserves predictive accuracy.",
            feature_set=list(features),
            feature_params=inherited_feature_params(lab, parent, features, metadata=metadata),
            model_type="ridge", hyperparameters=settings,
            hypothesis_group=f"curation_screen_{screen['method']}_{pid}", **common)

    ordered = sorted(features, key=lambda name: (name in BUILTIN_FEATURES,
                                                -int(metadata.get(name, {}).get("dim") or 1), name))
    blocks, seen = [], set()
    for name in ordered:
        dependencies = sorted(set(metadata.get(name, {}).get("dependencies") or []) & set(features))
        if dependencies:
            block = tuple(dict.fromkeys([name, *dependencies[:2]]))
            key = frozenset(block)
            if 1 < len(block) < len(features) and key not in seen:
                blocks.append(block)
                seen.add(key)
    for i in range(0, len(ordered) - 1, 2):
        block = tuple(ordered[i:i + 2])
        if len(block) < len(features) and frozenset(block) not in seen:
            blocks.append(block)
            seen.add(frozenset(block))
    removals = []
    for i, name in enumerate(ordered):
        removals.append((name,))
        if i < len(blocks):
            removals.append(blocks[i])
    for block in blocks[len(ordered):]:
        removals.append(block)
    for removed in removals:
        selected = [name for name in features if name not in removed]
        if not selected:
            continue
        params = inherited_feature_params(lab, parent, selected, metadata=metadata)
        if len(removed) + (params != (parent.get("feature_params_json") or {})) > 3:
            continue  # adhere to the same one-idea guard as every other proposal
        yield ExperimentSpec(
            hypothesis=f"Remove {' + '.join(removed)} from frozen incumbent {pid}.",
            scientific_rationale="A conditional module/block ablation tests redundancy and interactions; "
                                 "a negative result does not blacklist any constituent in other models.",
            feature_set=selected, feature_params=params, model_type=model,
            hyperparameters=deepcopy(hp), hypothesis_group=f"curation_drop_{'_'.join(removed)}_{pid}", **common)


class CurationScheduler:
    def __init__(self, lab, workers: int):
        self.lab = lab
        settings = lab.cfg.get("curation") or {}
        self.enabled = settings.get("enabled", False)
        if not isinstance(self.enabled, bool):
            raise ValueError("curation.enabled must be a boolean")
        self.reserved_workers = 0
        self.max_candidates = 32
        self.interval_s = 60.0
        self.next_round_at = 0.0
        self.parent_id = None
        self.round_ids: list[str] = []
        self.round_number = 0
        if not self.enabled:
            return
        from .model_selection import score_tolerance
        score_tolerance(lab.cfg)  # fail before any workers start, using the policy's validator
        reserved = settings.get("reserved_workers", 2)
        maximum = settings.get("max_candidates_per_round", 32)
        interval = settings.get("interval_s", 60.0)
        if workers < 2:
            raise ValueError("curation requires at least two workers so discovery retains a lane")
        if isinstance(reserved, bool) or not isinstance(reserved, int) or reserved < 1:
            raise ValueError("curation.reserved_workers must be a positive integer")
        if isinstance(maximum, bool) or not isinstance(maximum, int) or not 1 <= maximum <= 256:
            raise ValueError("curation.max_candidates_per_round must be an integer in [1,256]")
        if isinstance(interval, bool) or not isinstance(interval, (int, float)) or not math.isfinite(interval) or interval <= 0:
            raise ValueError("curation.interval_s must be positive and finite")
        self.reserved_workers = min(reserved, workers - 1)
        self.max_candidates, self.interval_s = maximum, float(interval)

    def lane(self, worker_index: int) -> str | None:
        if not self.enabled:
            return None
        return "curation" if worker_index < self.reserved_workers else "discovery"

    def maybe_queue(self, *, now: float | None = None, force: bool = False) -> list[str]:
        """Queue one bounded round even when discovery is busy; never overlap rounds.

        Existing pending curator work (including after a controller restart) keeps
        its original parent. Forced calls bypass the idle timer, not that barrier.
        Global config hashes suppress every previously attempted candidate.
        """
        if not self.enabled or self.lab.stop_event.is_set():
            return []
        pending = self.lab.db.query(
            f"SELECT experiment_id FROM experiments WHERE proposer=? AND status IN ({','.join('?' for _ in _PENDING)})",
            (PROPOSER, *_PENDING))
        if pending:
            return []
        now = time.time() if now is None else now
        if not force and now < self.next_round_at:
            return []
        self.next_round_at = now + self.interval_s
        # Copy only configuration fields: no labels or evaluation artifacts are read.
        best = self.lab.best()
        if best is None:
            return []
        parent = {key: deepcopy(best.get(key)) for key in (
            "experiment_id", "feature_set_json", "feature_params_json", "model_type", "hyperparameters_json", "seed")}
        tried = {row["config_hash"] for row in self.lab.db.query(
            "SELECT config_hash FROM experiments WHERE config_hash IS NOT NULL")}
        queued, attempts = [], 0
        for spec in candidates(self.lab, parent):
            digest = self.lab.config_hash_for(spec)
            if digest in tried:
                continue
            tried.add(digest)
            eid, status = self.lab.queue(spec)
            attempts += 1
            if status == "queued":
                queued.append(eid)
            if attempts >= self.max_candidates:
                break
        self.parent_id, self.round_ids = parent["experiment_id"], queued
        if attempts:
            self.round_number += 1
            self.lab.db.event("curation_round", json.dumps({"round": self.round_number,
                "parent": self.parent_id, "queued": queued, "attempted": attempts,
                "reserved_workers": self.reserved_workers}))
        return queued
