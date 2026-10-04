"""End-of-run research summary (markdown + machine-readable JSON)."""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

import numpy as np

from .benchmark.oracle import QueryBudgetExceeded


def _fmt(x, nd=4):
    return "n/a" if x is None else (f"{x:.{nd}f}" if isinstance(x, float) else str(x))


def run_query_only(lab, top_k: int, allow_new: bool = True) -> list[dict]:
    """Query-only (sealed-set) rows for the top-k visible winners plus the best baseline. With allow_new=False
    no new oracle query is made: only experiments already scored on the sealed set are reported, so a
    re-generated summary keeps its tables without spending query budget."""
    db = lab.db
    cands = db.query("SELECT * FROM experiments WHERE status='completed' AND kind NOT IN ('baseline', 'ensemble') "
                     "ORDER BY primary_score DESC")
    if not allow_new:
        cands = [c for c in cands if c.get("query_metrics_json")]
    seen, picked = set(), []
    for c in cands:
        key = json.dumps(sorted(c.get("feature_set_json") or [])) + c["model_type"]
        if key not in seen:
            seen.add(key)
            picked.append(c)
        if len(picked) >= top_k:
            break
    # query order: the single finalists, then the starting model, then the ensemble; so a query cap of
    # top_k + 1 still scores the baseline and the ensemble is the one left out
    singles = list(picked)
    base = lab.best_baseline()
    if base and (allow_new or base.get("query_metrics_json")):
        picked.append(base)
    ens = None
    if allow_new and lab.cfg.get("final", {}).get("ensemble", True):
        try:
            ens = ensemble_finalist(lab, singles)
        except Exception as exc:  # a damaged member artifact must not lose the report
            db.event("ensemble_error", f"{type(exc).__name__}: {exc}"[:300], level="warning")
    elif not allow_new:
        ens = next(iter(db.query("SELECT * FROM experiments WHERE kind='ensemble' AND status='completed' "
                                 "AND query_metrics_json IS NOT NULL LIMIT 1")), None)
    if ens is not None:
        picked.append(ens)
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
               "members": ((c.get("diagnostics_json") or {}).get("members") if c["kind"] == "ensemble" else None),
               "visible_score": c["primary_score"], "query_only_score": q["metrics"]["primary"],
               "gap": c["primary_score"] - q["metrics"]["primary"],
               "query_only_pearson_delta": q["metrics"].get("pearson_delta"),  # by name, whatever the rule
               "comparable": {"val1": {k: v for k, v in (c.get("val_metrics_json") or {}).items()
                                       if k.startswith(COMPARABLE_PREFIXES)},
                              "val2": {k: v for k, v in q["metrics"].items() if k.startswith(COMPARABLE_PREFIXES)}}}
        try:
            v1 = lab.celleval_val1(c["experiment_id"])
        except Exception as exc:  # cell-eval is a report extra; never lose the report over it
            db.event("celleval_error", f"{type(exc).__name__}: {exc}"[:300], c["experiment_id"], "warning")
            v1 = None
        if v1 is not None:
            row["cell_eval"] = {"val1": v1, "val2": lab.celleval_val2(c["experiment_id"])}
        out.append(row)
    # shown by visible score (the headline is whichever wins on the visible perturbations), baseline last
    out.sort(key=lambda r: (r["kind"] == "baseline", -(r["visible_score"] or 0)))
    return out


COMPARABLE_PREFIXES = ("cellforge_", "vcworld_")
CELLFORGE_SHOWN = ("cellforge_mse", "cellforge_pcc", "cellforge_r2", "cellforge_mse_de", "cellforge_pcc_de",
                   "cellforge_r2_de")
VCWORLD_SHOWN = ("vcworld_de_f1", "vcworld_de_auroc", "vcworld_de_auprc", "vcworld_dir_accuracy",
                 "vcworld_dir_f1", "vcworld_dir_auroc")
CELLEVAL_SHOWN = ("pearson_delta", "mse", "discrimination_score_l1", "overlap_at_N", "de_direction_match")


def ensemble_finalist(lab, members: list[dict]) -> dict | None:
    """One more finalist: the average of the finalists' predicted deltas (an average of linear models is
    itself linear in the union of their features). It is scored like any experiment on the visible
    perturbations and kept, as a completed experiment of kind 'ensemble', only when it beats the best single
    member there; so it costs at most one query-only evaluation and never replaces a better single model.
    Built once per run; a re-summary finds the stored record."""
    existing = lab.db.query("SELECT * FROM experiments WHERE kind='ensemble' AND status='completed' LIMIT 1")
    if existing:
        return existing[0]
    members = [m for m in members if m.get("artifact_dir") and m.get("primary_score") is not None]
    if len(members) < 2:
        return None

    def chosen(path, alpha):
        z = np.load(path, allow_pickle=False)
        alphas = list(map(float, z["alphas"]))
        k = alphas.index(float(alpha)) if float(alpha) in alphas else 0
        return [str(p) for p in z["perts"]], z["delta"][k].astype(np.float64), z

    deltas, cvs, perts_ref, cv_perts = [], [], None, None
    for m in members:
        perts, d, _ = chosen(Path(m["artifact_dir"]) / "predictions.npz", m["best_alpha"])
        if perts_ref is None:
            perts_ref = perts
        elif perts != perts_ref:
            lab.db.event("ensemble_skipped", "finalists predict different perturbation sets", level="warning")
            return None
        deltas.append(d)
        if lab.cv_folds > 1:
            cvp = Path(m["artifact_dir"]) / "cv.npz"
            if not cvp.exists():
                return None
            cv_perts, c, _ = chosen(cvp, m["best_alpha"])
            cvs.append(c)
    ids = [m["experiment_id"] for m in members]
    eid = lab.db.next_experiment_id()
    art = lab.artifacts / eid
    kept = False
    try:
        art.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(art / "predictions.npz", delta=np.mean(deltas, axis=0)[None].astype(np.float32),
                            perts=np.array(perts_ref), alphas=np.array([0.0]))
        if cvs:
            np.savez_compressed(art / "cv.npz", delta=np.mean(cvs, axis=0)[None].astype(np.float32),
                                perts=np.array(cv_perts), alphas=np.array([0.0]), folds=np.array([lab.cv_folds]))
        try:
            ev = lab.evaluate_artifact(art / "predictions.npz")
        except ValueError as exc:
            lab.db.event("ensemble_skipped", str(exc)[:300], level="warning")
            return None
        best_single = max(m["primary_score"] for m in members)
        if ev["metrics"]["primary"] <= best_single:
            lab.db.event("ensemble_skipped", f"average of {', '.join(ids)} scores {ev['metrics']['primary']:.4f} on "
                         f"the visible perturbations, not above the best single model ({best_single:.4f})")
            return None
        kept = True
    finally:
        if not kept:  # nothing half-built survives: no artifact, no reserved id
            shutil.rmtree(art, ignore_errors=True)
            lab.db.execute("DELETE FROM experiments WHERE experiment_id=? AND status='reserved'", (eid,))
    feature_set = sorted(set().union(*[set(m.get("feature_set_json") or []) for m in members]))
    lab.db.insert_experiment({
        "experiment_id": eid, "run_id": lab.run_id, "status": "completed", "kind": "ensemble",
        "category": "exploit", "hypothesis": f"Average of the predictions of the top finalists {', '.join(ids)}.",
        "rationale": "Averaging independently selected linear models cancels part of their selection noise; "
                     "the result is still a linear model in the union of their features.",
        "hypothesis_group": "ensemble_top_finalists", "feature_set_json": feature_set, "model_type": "ensemble",
        "parent_id": members[0]["experiment_id"], "dataset": lab.dataset, "split_id": lab.split_id,
        "proposer": "python:ensemble", "provider": "python", "model": "ensemble",
        "val_metrics_json": {**ev["metrics"], "alpha_scores": ev["alpha_scores"]},
        "diagnostics_json": {**ev["diagnostics"], "members": ids}, "primary_score": ev["metrics"]["primary"],
        "parent_score": best_single, "delta_from_parent": ev["metrics"]["primary"] - best_single,
        "best_alpha": 0.0, "artifact_dir": str(art), "finished_at": time.time(), "code_commit": lab.base_commit,
        "seed": 0})
    lab.db.event("ensemble", f"{eid}: average of {', '.join(ids)} scores {ev['metrics']['primary']:.4f} vs best "
                 f"single {best_single:.4f} on the visible perturbations", eid)
    return lab.db.get_experiment(eid)


def planner_health(lab, started_at: float | None) -> dict:
    """Which planners actually produced the run's plans, in order of first use, with every switch and
    failure, from the database (so a re-summary of a killed run says the same). A run whose `used` list
    differs from `configured` ran on a fallback for part or all of its time and is a mixed-planner arm."""
    db = lab.db
    p = lab.cfg.get("planner") or {}
    rounds = db.query("SELECT provider, model, COUNT(*) n, COALESCE(SUM(n_queued), 0) queued FROM planner_rounds "
                      "GROUP BY provider, model ORDER BY MIN(id)")
    t0 = started_at or 0.0
    switches = [{"at_min": round((e["ts"] - t0) / 60, 1), "note": e["message"]}
                for e in db.query("SELECT ts, message FROM events WHERE kind='planner_switch' ORDER BY ts")]
    exhausted = db.query("SELECT ts, message FROM events WHERE kind='planner_exhausted' ORDER BY ts LIMIT 1")
    failed = db.query("SELECT COUNT(*) n FROM events WHERE kind IN ('planner_error', 'planner_crash')")[0]["n"]
    return {"configured": f"{p.get('provider', '?')}:{p.get('model', '')}",
            "fallback": p.get("fallback") or [],
            "used": [f"{r['provider']}:{r['model']}" for r in rounds],
            "rounds": {f"{r['provider']}:{r['model']}": {"rounds": r["n"], "queued": r["queued"]} for r in rounds},
            "switches": switches, "failed_rounds": failed,
            "exhausted_at_min": None if not exhausted else round((exhausted[0]["ts"] - t0) / 60, 1),
            "mixed": bool(switches) or bool(exhausted)}


def build_summary(lab, wall_s: float | None, workers: int | None, generalization: list[dict] | None) -> dict:
    db = lab.db
    exps = db.query("SELECT * FROM experiments WHERE status NOT IN ('reserved')")
    by = {}
    for e in exps:
        by.setdefault(e["status"], []).append(e)
    done = by.get("completed", [])
    run = db.query("SELECT * FROM runs LIMIT 1")[0]
    duration_note = None
    end = run.get("finished_at")
    if end is None:  # the run never shut down (it was killed): its wall time is at most the deadline plus the grace period
        grace = float((lab.cfg.get("run") or {}).get("shutdown_grace_s") or 0)
        end = min(time.time(), (run.get("deadline") or time.time()) + grace)
        duration_note = "the run was cut before it wrote its summary; its duration is capped at its deadline"
    if wall_s is None:
        wall_s = end - (run.get("started_at") or end)
    best = lab.best()
    base = lab.best_baseline()
    proposed = [e for e in exps if e["kind"] not in ("baseline", "ensemble")]
    ensemble = next((e for e in done if e["kind"] == "ensemble"), None)
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
    counted = [e for e in done if e["kind"] not in ("baseline", "ensemble")]  # what the efficiency rates count
    by_proposer = {}
    for e in counted:
        by_proposer[e.get("proposer") or "planner"] = by_proposer.get(e.get("proposer") or "planner", 0) + 1
    planner_only = [e for e in counted if not (e.get("proposer") or "").startswith("python:")]
    planner_groups = {e.get("hypothesis_group") for e in proposed if not (e.get("proposer") or "").startswith("python:")}
    planner = planner_health(lab, run.get("started_at"))
    summary = {
        "run_id": lab.run_id, "dataset": lab.dataset, "split_id": lab.split_id, "base_commit": lab.base_commit,
        "duration_s": round(wall_s, 1), "duration_note": duration_note, "finished_at": end,
        "workers": workers or run.get("workers"),
        "continued_from": lab.cfg["run"].get("continue_from"),
        "selection": {"rule": lab.selection, "cv_folds": lab.cv_folds, "n_validation": len(lab._val1.perts),
                      "n_visible": len(lab._val1.perts) + (len(lab._train.perts) if lab.cv_folds > 1 else 0)},
        "experiments_proposed": len(proposed),
        "experiments_completed": len(counted),
        "completed_by_proposer": by_proposer,  # "planner" (LLM or scripted) vs python:exploit, python:warm_start
        "experiments_completed_planner": len(planner_only),
        "unique_hypotheses_planner": len(planner_groups),
        "experiments_failed": len(by.get("failed", [])), "experiments_rejected": len(by.get("rejected", [])),
        "experiments_killed": len(by.get("killed", [])), "experiments_cancelled": len(by.get("cancelled", [])),
        "duplicate_experiments": len(by.get("duplicate", [])),
        "unique_hypotheses": len(groups), "replicated_hypotheses": len(replicate_groups),
        "cpu_hours": round(cpu_s / 3600, 4),
        "llm_usage": {"all": llm, "worker": llm_w, "planner": llm_p},
        "planner": planner,
        "baseline": None if not base else {"experiment_id": base["experiment_id"], "score": base["primary_score"],
                                           "description": base["hypothesis"]},
        "best": None if not best else {
            "experiment_id": best["experiment_id"], "score": best["primary_score"], "model": best["model_type"],
            "alpha": best["best_alpha"], "features": best.get("feature_set_json"),
            "metrics": best.get("val_metrics_json"),
            "coefficients": (best.get("diagnostics_json") or {}).get("coefficients")},
        "improvement_over_baseline": gain,
        "ensemble": None if not ensemble else {
            "experiment_id": ensemble["experiment_id"], "members": (ensemble.get("diagnostics_json") or {}).get("members"),
            "score": ensemble["primary_score"], "features": ensemble.get("feature_set_json"),
            "query_only_score": (ensemble.get("query_metrics_json") or {}).get("primary")},
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
            "experiments_per_hour": round(len(counted) / hours, 2),
            "planner_experiments_per_hour": round(len(planner_only) / hours, 2),
            "mean_cpu_s_per_experiment": round(cpu_s / max(1, len(counted)), 2),
            "gain_per_cpu_hour": None if gain is None or cpu_s == 0 else gain / (cpu_s / 3600),
            "gain_per_usd": None if gain is None or not llm["cost_usd"] else gain / llm["cost_usd"],
            "cost_per_completed_experiment_usd": llm["cost_usd"] / max(1, len(counted)),
        },
        "reproduction_command": None if not best else
            f"python reproduce.py --run {lab.run_dir} --experiment {best['experiment_id']}",
    }
    return summary


def render_markdown(s: dict) -> str:
    L = ["# RUN SUMMARY", "",
         f"Run `{s['run_id']}` on dataset `{s['dataset']}` (split `{s['split_id']}`, code `{s['base_commit'][:10]}`)", "",
         f"- Duration: {s['duration_s'] / 60:.1f} min" + (f" ({s['duration_note']})" if s.get("duration_note") else ""),
         f"- Workers: {s['workers']}",
         f"- Experiments proposed: {s['experiments_proposed']}",
         f"- Experiments completed: {s['experiments_completed']} (plus baselines; "
         + ", ".join(f"{k}: {v}" for k, v in sorted((s.get('completed_by_proposer') or {}).items())) + ")",
         f"- Experiments failed / rejected / killed / not started: {s['experiments_failed']} / "
         f"{s['experiments_rejected']} / {s['experiments_killed']} / {s['experiments_cancelled']}",
         f"- Unique hypotheses: {s['unique_hypotheses']} (replicated: {s['replicated_hypotheses']}); "
         f"duplicate configurations skipped: {s['duplicate_experiments']}",
         f"- CPU hours: {s['cpu_hours']:.4f}"]
    for role in ("worker", "planner"):
        u = s["llm_usage"][role]
        L.append(f"- LLM ({role}): {u['calls']} calls, {u['input_tokens']} in / {u['output_tokens']} out / "
                 f"{u['cached_tokens']} cached tokens, ${u['cost_usd']:.4f}")
    ph = s.get("planner") or {}
    if ph.get("mixed"):
        L.append(f"- PLANNER CHANGED DURING THE RUN (mixed-planner arm): configured {ph['configured']}, used "
                 f"{' -> '.join(ph['used']) or 'none'}; " + "; ".join(f"at {sw['at_min']} min: {sw['note']}" for sw in ph["switches"])
                 + (f"; no planner left after {ph['exhausted_at_min']} min" if ph.get("exhausted_at_min") is not None else ""))
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
    ens = s.get("ensemble")
    L += ["", "## ENSEMBLE FINALIST"]
    if ens:
        L += [f"{ens['experiment_id']}: average of {', '.join(ens['members'] or [])} scores {_fmt(ens['score'])} on the "
              f"visible perturbations (query-only {_fmt(ens['query_only_score'])}). It is a finalist, not the best "
              "single model; the union of its members' features is listed in summary.json."]
    else:
        L += ["- none kept (the average of the finalists did not beat the best single model, or ensembles are off)"]
    L += ["", "## GENERALIZATION TO QUERY-ONLY VALIDATION", "| experiment | kind | visible | query-only | gap |",
          "|---|---|---|---|---|"]
    L += [f"| {g['experiment_id']} | {g['kind']} | {g['visible_score']:.4f} | {g['query_only_score']:.4f} | "
          f"{g['gap']:+.4f} |" for g in s["generalization_query_only"]]
    comp = [g for g in s["generalization_query_only"] if (g.get("comparable") or {}).get("val1")]
    for title, shown, note in [
            ("CELLFORGE METRICS (visible / query-only)", CELLFORGE_SHOWN,
             "Mean expression per perturbation, all genes and top-20 DE genes (CellForge, Table 1)."),
            ("VCWORLD METRICS (visible / query-only)", VCWORLD_SHOWN,
             "DE: Wilcoxon BH p<=0.05 and |log2FC|>=0.25 over (perturbation, gene) pairs; DIR: up/down on "
             "true DE genes; a prediction's log2FC decides both (VCWorld).")]:
        if not comp:
            break
        L += ["", f"## {title}", note, "", "| experiment | " + " | ".join(m.split("_", 1)[1] for m in shown) + " |",
              "|---|" + "---|" * len(shown)]
        for g in comp:
            v1, v2 = g["comparable"]["val1"], g["comparable"]["val2"]
            L.append(f"| {g['experiment_id']} | " + " | ".join(f"{_fmt(v1.get(m), 3)} / {_fmt(v2.get(m), 3)}"
                                                                for m in shown) + " |")
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
    """query=True evaluates the winners on the sealed set (capped); query=False only reuses stored scores."""
    gen = run_query_only(lab, int(lab.cfg.get("final", {}).get("top_k", 3)), allow_new=query)
    s = build_summary(lab, wall_s, workers, gen)
    # a later summarize.py must not move the run's end (throughput and cost rates are measured against it)
    lab.db.execute("UPDATE runs SET finished_at=COALESCE(finished_at, ?), summary_json=? WHERE run_id=?",
                   (s.get("finished_at") or time.time(), json.dumps(s, default=str), lab.run_id))
    (Path(lab.run_dir) / "summary.json").write_text(json.dumps(s, indent=1, default=str))
    (Path(lab.run_dir) / "summary.md").write_text(render_markdown(s))
    return s
