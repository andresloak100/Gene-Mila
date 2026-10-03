"""End-of-run research summary (markdown + machine-readable JSON)."""

from __future__ import annotations

import json
import time
from pathlib import Path

from .benchmark.oracle import QueryBudgetExceeded


def _fmt(x, nd=4):
    return "n/a" if x is None else (f"{x:.{nd}f}" if isinstance(x, float) else str(x))


def run_query_only(lab, top_k: int) -> list[dict]:
    db = lab.db
    cands = db.query("SELECT * FROM experiments WHERE status='completed' AND kind!='baseline' "
                     "ORDER BY primary_score DESC")
    seen, picked = set(), []
    for c in cands:
        key = json.dumps(sorted(c.get("feature_set_json") or [])) + c["model_type"]
        if key not in seen:
            seen.add(key)
            picked.append(c)
        if len(picked) >= top_k:
            break
    base = lab.best_baseline()
    if base:
        picked.append(base)
    out = []
    for c in picked:
        try:
            if c.get("query_metrics_json"):
                q = {"metrics": c["query_metrics_json"]}
            else:
                q = lab.query_only(c["experiment_id"])
        except QueryBudgetExceeded:
            break
        except Exception as exc:  # never lose the report over one candidate
            db.event("query_only_error", str(exc), c["experiment_id"], "warning")
            continue
        row = {"experiment_id": c["experiment_id"], "kind": c["kind"],
               "visible_score": c["primary_score"], "query_only_score": q["metrics"]["primary"],
               "gap": c["primary_score"] - q["metrics"]["primary"]}
        try:
            v1 = lab.celleval_val1(c["experiment_id"])
        except Exception as exc:  # cell-eval is a report extra; never lose the report over it
            db.event("celleval_error", f"{type(exc).__name__}: {exc}"[:300], c["experiment_id"], "warning")
            v1 = None
        if v1 is not None:
            row["cell_eval"] = {"val1": v1, "val2": lab.celleval_val2(c["experiment_id"])}
        out.append(row)
    return out


CELLEVAL_SHOWN = ("pearson_delta", "mse", "discrimination_score_l1", "overlap_at_N", "de_direction_match")


def build_summary(lab, wall_s: float | None, workers: int | None, generalization: list[dict] | None) -> dict:
    db = lab.db
    exps = db.query("SELECT * FROM experiments WHERE status NOT IN ('reserved')")
    by = {}
    for e in exps:
        by.setdefault(e["status"], []).append(e)
    done = by.get("completed", [])
    run = db.query("SELECT * FROM runs LIMIT 1")[0]
    wall_s = wall_s or ((run.get("finished_at") or time.time()) - (run.get("started_at") or time.time()))
    best = lab.best()
    base = lab.best_baseline()
    proposed = [e for e in exps if e["kind"] != "baseline"]
    groups = {}
    for e in proposed:
        groups.setdefault(e.get("hypothesis_group"), []).append(e)
    replicate_groups = {g: v for g, v in groups.items() if len(v) > 1}
    lineage = db.lineage(best["experiment_id"]) if best else []
    feats = {f["name"]: f for f in db.features()}
    new_feat_exps = [e for e in done if e.get("new_feature")]
    useful = sorted([e for e in new_feat_exps if (e["delta_from_parent"] or 0) > 0],
                    key=lambda e: -e["delta_from_parent"])
    failed_feats = [e for e in exps if e["kind"] == "new_feature" and e["status"] in ("failed", "rejected")]
    surprising = []
    for g, v in replicate_groups.items():
        scores = [e["primary_score"] for e in v if e["primary_score"] is not None]
        if len(scores) > 1 and max(scores) - min(scores) > 0.01:
            surprising.append(f"Replicates of '{v[0]['hypothesis'][:60]}' diverged: scores {', '.join(f'{s:.4f}' for s in scores)}"
                              " (implementation choices matter)")
    for e in new_feat_exps:
        if e["delta_from_parent"] is not None and e["delta_from_parent"] < -0.01:
            surprising.append(f"{e['new_feature']} made the model worse ({e['delta_from_parent']:+.4f}) despite "
                              "a linear model being able to ignore it (overfitting or scale issue)")
    cpu_s = sum(e.get("cpu_s") or 0 for e in exps)
    llm = db.llm_totals()
    llm_w, llm_p = db.llm_totals("worker"), db.llm_totals("planner")
    gain = (best["primary_score"] - base["primary_score"]) if best and base else None
    hours = max(wall_s, 1) / 3600
    summary = {
        "run_id": lab.run_id, "dataset": lab.dataset, "split_id": lab.split_id, "base_commit": lab.base_commit,
        "duration_s": round(wall_s, 1), "workers": workers or run.get("workers"),
        "experiments_proposed": len(proposed), "experiments_completed": len([e for e in done if e["kind"] != "baseline"]),
        "experiments_failed": len(by.get("failed", [])), "experiments_rejected": len(by.get("rejected", [])),
        "experiments_killed": len(by.get("killed", [])), "experiments_cancelled": len(by.get("cancelled", [])),
        "duplicate_experiments": len(by.get("duplicate", [])),
        "unique_hypotheses": len(groups), "replicated_hypotheses": len(replicate_groups),
        "cpu_hours": round(cpu_s / 3600, 4),
        "llm_usage": {"all": llm, "worker": llm_w, "planner": llm_p},
        "baseline": None if not base else {"experiment_id": base["experiment_id"], "score": base["primary_score"],
                                           "description": base["hypothesis"]},
        "best": None if not best else {
            "experiment_id": best["experiment_id"], "score": best["primary_score"], "model": best["model_type"],
            "alpha": best["best_alpha"], "features": best.get("feature_set_json"),
            "metrics": best.get("val_metrics_json"),
            "coefficients": (best.get("diagnostics_json") or {}).get("coefficients")},
        "improvement_over_baseline": gain,
        "lineage": [{"experiment_id": e["experiment_id"], "added": e.get("new_feature") or e["kind"],
                     "score": e["primary_score"], "hypothesis": e["hypothesis"]} for e in lineage],
        "most_useful_features": [{"feature": e["new_feature"], "experiment_id": e["experiment_id"],
                                  "delta": e["delta_from_parent"],
                                  "description": feats.get(e["new_feature"], {}).get("description")}
                                 for e in useful[:10]],
        "features_not_helping": [{"feature": e["new_feature"], "delta": e["delta_from_parent"]}
                                 for e in new_feat_exps if (e["delta_from_parent"] or 0) <= 0],
        "failed_features": [{"experiment_id": e["experiment_id"], "feature": e.get("new_feature"),
                             "stage": e["failure_stage"], "reason": (e["failure_reason"] or "")[:200]}
                            for e in failed_feats],
        "surprising_results": surprising,
        "generalization_query_only": generalization or [],
        "compute_efficiency": {
            "experiments_per_hour": round(len(done) / hours, 2),
            "mean_cpu_s_per_experiment": round(cpu_s / max(1, len(done)), 2),
            "gain_per_cpu_hour": None if gain is None or cpu_s == 0 else gain / (cpu_s / 3600),
            "gain_per_usd": None if gain is None or not llm["cost_usd"] else gain / llm["cost_usd"],
            "cost_per_completed_experiment_usd": llm["cost_usd"] / max(1, len(done)),
        },
        "reproduction_command": None if not best else
            f"python reproduce.py --run {lab.run_dir} --experiment {best['experiment_id']}",
    }
    return summary


def render_markdown(s: dict) -> str:
    L = ["# RUN SUMMARY", "",
         f"Run `{s['run_id']}` on dataset `{s['dataset']}` (split `{s['split_id']}`, code `{s['base_commit'][:10]}`)", "",
         f"- Duration: {s['duration_s'] / 60:.1f} min",
         f"- Workers: {s['workers']}",
         f"- Experiments proposed: {s['experiments_proposed']}",
         f"- Experiments completed: {s['experiments_completed']} (plus baselines)",
         f"- Experiments failed / rejected / killed / not started: {s['experiments_failed']} / "
         f"{s['experiments_rejected']} / {s['experiments_killed']} / {s['experiments_cancelled']}",
         f"- Unique hypotheses: {s['unique_hypotheses']} (replicated: {s['replicated_hypotheses']}); "
         f"duplicate configurations skipped: {s['duplicate_experiments']}",
         f"- CPU hours: {s['cpu_hours']:.4f}"]
    for role in ("worker", "planner"):
        u = s["llm_usage"][role]
        L.append(f"- LLM ({role}): {u['calls']} calls, {u['input_tokens']} in / {u['output_tokens']} out / "
                 f"{u['cached_tokens']} cached tokens, ${u['cost_usd']:.4f}")
    b, best = s["baseline"], s["best"]
    L += ["", "## BASELINE PERFORMANCE", f"{b['experiment_id']}: {b['description']} pearson_delta = {b['score']:.4f}"
          if b else "n/a", "", "## BEST PERFORMANCE"]
    if best:
        L += [f"{best['experiment_id']}: pearson_delta = {best['score']:.4f} ({best['model']}, alpha={best['alpha']})",
              "", "## IMPROVEMENT", f"{_fmt(s['improvement_over_baseline'])} over the best baseline", "",
              "## BEST MODEL / FEATURES INCLUDED"]
        for k, v in sorted((best.get("coefficients") or {}).items(), key=lambda kv: -abs(kv[1])):
            L.append(f"- {k}: coefficient {v:+.4f}")
        L += ["", "## DISCOVERY LINEAGE"]
        for i, e in enumerate(s["lineage"]):
            L.append(f"{'    ' * i}{'↳ ' if i else ''}{e['experiment_id']} [{e['added']}] score {_fmt(e['score'])}")
    L += ["", "## MOST USEFUL FEATURES"]
    L += [f"- {f['feature']} ({f['experiment_id']}): {f['delta']:+.4f}. {f['description'] or ''}"
          for f in s["most_useful_features"]] or ["- none"]
    L += ["", "## FEATURES THAT DID NOT HELP"]
    L += [f"- {f['feature']}: {_fmt(f['delta'])}" for f in s["features_not_helping"]] or ["- none"]
    L += ["", "## FAILED FEATURES"]
    L += [f"- {f['experiment_id']} {f['feature']} [{f['stage']}]: {f['reason']}" for f in s["failed_features"]] or ["- none"]
    L += ["", "## SURPRISING RESULTS"] + ([f"- {x}" for x in s["surprising_results"]] or ["- none"])
    L += ["", "## GENERALIZATION TO QUERY-ONLY VALIDATION", "| experiment | kind | visible | query-only | gap |",
          "|---|---|---|---|---|"]
    L += [f"| {g['experiment_id']} | {g['kind']} | {g['visible_score']:.4f} | {g['query_only_score']:.4f} | "
          f"{g['gap']:+.4f} |" for g in s["generalization_query_only"]]
    rows = [g for g in s["generalization_query_only"] if g.get("cell_eval")]
    if rows:
        L += ["", "## CELL-EVAL (visible / query-only)",
              "Predicted means repeated per cell, anchored on held-out control cells; full metrics in summary.json "
              "and runs/<run>/celleval/.", "",
              "| experiment | " + " | ".join(CELLEVAL_SHOWN) + " |", "|---|" + "---|" * len(CELLEVAL_SHOWN)]
        for g in rows:
            v1, v2 = g["cell_eval"]["val1"] or {}, g["cell_eval"]["val2"] or {}
            L.append(f"| {g['experiment_id']} | " + " | ".join(f"{_fmt(v1.get(m), 3)} / {_fmt(v2.get(m), 3)}"
                                                                for m in CELLEVAL_SHOWN) + " |")
    ce = s["compute_efficiency"]
    L += ["", "## COMPUTE EFFICIENCY", f"- Experiments/hour: {ce['experiments_per_hour']}",
          f"- Mean CPU s/experiment: {ce['mean_cpu_s_per_experiment']}",
          f"- Gain per CPU-hour: {_fmt(ce['gain_per_cpu_hour'])}", f"- Gain per USD: {_fmt(ce['gain_per_usd'])}",
          f"- LLM cost per completed experiment: ${ce['cost_per_completed_experiment_usd']:.5f}",
          "", "## REPRODUCTION COMMAND", f"`{s['reproduction_command']}`", ""]
    return "\n".join(L)


def finalize(lab, wall_s: float | None = None, workers: int | None = None, query: bool = True) -> dict:
    gen = run_query_only(lab, int(lab.cfg.get("final", {}).get("top_k", 3))) if query else None
    s = build_summary(lab, wall_s, workers, gen)
    lab.db.execute("UPDATE runs SET finished_at=?, summary_json=? WHERE run_id=?",
                   (time.time(), json.dumps(s, default=str), lab.run_id))
    (Path(lab.run_dir) / "summary.json").write_text(json.dumps(s, indent=1, default=str))
    (Path(lab.run_dir) / "summary.md").write_text(render_markdown(s))
    return s
