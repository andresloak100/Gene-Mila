"""Compressed research memory, generated deterministically from the database.

The planner never sees raw history: it sees this summary, whose size is
bounded regardless of how many experiments have run.
"""

from __future__ import annotations

import itertools
import json
import time

from .db import ACTIVE
from .lab import Lab

HELP_THRESHOLD = 0.002  # minimum primary-metric gain to call a feature "helpful"

IDEA_BANK = [
    ("target co-expression", ("coexpr", "correl")),
    ("perturbation similarity / nearest-neighbour response transfer", ("similar", "knn", "neighbo", "transfer")),
    ("prior regulatory network / TF targets", ("network", "edge", "regulat", "tf_")),
    ("pathway or gene-set membership", ("module", "pathway", "gene_set", "set")),
    ("PCA / latent programs of control cells", ("pca", "latent", "svd", "program")),
    ("network centrality / graph diffusion from the target", ("central", "diffus", "propagat", "graph")),
    ("partial correlation / sparse graphical model", ("partial", "graphical", "precision")),
    ("gene expression level transforms (log, rank, dropout rate)", ("rank", "dropout", "log_", "zero")),
    ("target knockdown magnitude", ("target_level", "knockdown", "self")),
    ("interaction of existing features", ("interact", "product", "x_")),
    ("response heterogeneity across training perturbations (gene responsiveness)", ("respons", "variab", "std")),
]


def _short(text: str, n: int = 90) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= n else text[: n - 1] + "…"


def build_state(lab: Lab, max_recent: int = 10) -> dict:
    db = lab.db
    exps = db.query("SELECT * FROM experiments WHERE status!='reserved' ORDER BY created_at")
    done = [e for e in exps if e["status"] == "completed"]
    baselines = [e for e in done if e["kind"] == "baseline"]
    best = lab.best()
    best_base = max(baselines, key=lambda e: e["primary_score"], default=None)
    features = {f["name"]: f for f in db.features()}

    feat_stats = {}
    for e in done:
        nf = e.get("new_feature")
        if nf:
            feat_stats.setdefault(nf, []).append(e)
    helpful, unhelpful = [], []
    for name, rows in feat_stats.items():
        deltas = [r["delta_from_parent"] for r in rows if r["delta_from_parent"] is not None]
        d = max(deltas) if deltas else None
        item = {"feature": name, "experiment": rows[0]["experiment_id"], "delta": d,
                "score": rows[0]["primary_score"],
                "description": _short(features.get(name, {}).get("description", ""), 80)}
        (helpful if d is not None and d > HELP_THRESHOLD else unhelpful).append(item)
    helpful.sort(key=lambda x: -x["delta"])

    failed = [e for e in exps if e["status"] in ("failed", "rejected", "killed")]
    failed_lines = [{"experiment": e["experiment_id"], "idea": _short(e["hypothesis"], 70),
                     "stage": e["failure_stage"], "reason": _short(e["failure_reason"], 110)} for e in failed[-12:]]

    best_set = set((best or {}).get("feature_set_json") or [])
    helpful_names = [h["feature"] for h in helpful]
    combined = {frozenset(e.get("feature_set_json") or []) for e in done}
    interactions = []
    for a, b in itertools.combinations(helpful_names[:8], 2):
        if not any({a, b} <= s for s in combined):
            interactions.append(f"{a} + {b}")
    untested_helpful_in_best = [h for h in helpful_names if h not in best_set]

    used_text = " ".join(f"{e.get('new_feature') or ''} {e['hypothesis']}".lower() for e in exps)
    unexplored = [idea for idea, keys in IDEA_BANK if not any(k in used_text for k in keys)]

    inflight = [e for e in exps if e["status"] in ("queued", *ACTIVE)]
    recent = [{"id": e["experiment_id"], "status": e["status"], "kind": e["kind"], "cat": e["category"],
               "idea": _short(e["hypothesis"], 70),
               "score": None if e["primary_score"] is None else round(e["primary_score"], 4),
               "delta": None if e["delta_from_parent"] is None else round(e["delta_from_parent"], 4)}
              for e in sorted([e for e in exps if e["status"] not in ("queued", *ACTIVE)],
                              key=lambda e: e.get("finished_at") or 0)[-max_recent:]]
    cpu = [e["cpu_s"] for e in done if e.get("cpu_s")]
    llm = db.llm_totals()
    return {
        "generated_at": time.time(),
        "dataset": lab.data_summary(),
        "primary_metric": "pearson_delta (higher is better): mean over held-out perturbations of the Pearson "
                          "correlation between predicted and true expression change",
        "knowledge_available": lab.knowledge_summary(),
        "baselines": [{"id": e["experiment_id"], "what": _short(e["hypothesis"], 60),
                       "score": round(e["primary_score"], 4)} for e in baselines],
        "current_best": None if not best else {
            "id": best["experiment_id"], "score": round(best["primary_score"], 4),
            "features": best.get("feature_set_json"), "model": best["model_type"], "alpha": best["best_alpha"],
            "gain_over_best_baseline": None if not best_base else round(best["primary_score"] - best_base["primary_score"], 4),
            "coefficients": (best.get("diagnostics_json") or {}).get("coefficients"),
            "diagnostics": {k: v for k, v in (best.get("diagnostics_json") or {}).items() if k != "coefficients"},
        },
        "feature_registry": [f"{n}: {_short(f.get('description', ''), 70)}" for n, f in features.items()],
        "features_that_help": helpful[:10],
        "features_that_do_not_help": unhelpful[:12],
        "helpful_features_missing_from_best": untested_helpful_in_best[:8],
        "possible_interactions_untested": interactions[:8],
        "failed_directions": failed_lines,
        "unexplored_idea_areas": unexplored,
        "in_flight": [_short(e["hypothesis"], 70) for e in inflight][:20],
        "recent_experiments": recent,
        "compute": {"completed": len(done), "failed": len(failed), "mean_cpu_s": round(sum(cpu) / len(cpu), 2) if cpu else None,
                    "llm_calls": llm["calls"], "llm_cost_usd": round(llm["cost_usd"], 4)},
    }


def render_state(state: dict) -> str:
    """Compact text for the planner. Bounded size."""
    out = []
    for key, value in state.items():
        if key == "generated_at":
            continue
        title = key.replace("_", " ").upper()
        if isinstance(value, list):
            out.append(f"## {title}")
            out += [f"- {json.dumps(v) if isinstance(v, dict) else v}" for v in value] or ["- (none)"]
        elif isinstance(value, dict):
            out.append(f"## {title}\n{json.dumps(value, separators=(',', ':'))}")
        else:
            out.append(f"## {title}\n{value}")
    text = "\n".join(out)
    return text[:12000]
