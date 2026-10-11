#!/usr/bin/env python3
"""How high can pearson_delta go on a dataset? A noise ceiling from cell-sampling noise, on visible data only.

pearson_delta scores a prediction against the mean expression of a finite sample of perturbed cells. That mean
is the true expected response plus the sampling noise of n cells, so even a predictor that knew the true
response exactly would not reach a correlation of 1: the metric has a ceiling set by the data, and the gap
between a run's score and that ceiling bounds what any predictor could still add. The ceiling is
estimated here from the visible validation perturbations' held-out cells and the public control cells (the
same vector the lab subtracts as control_mean). The sealed set is never touched.

Method, per visible-validation perturbation p with n cells, repeated R times with a fixed seed:

1. Split its cells at random into two halves A and B. delta_A = mean(A) - control_mean and delta_B = mean(B) -
   control_mean; r_half = Pearson(delta_A, delta_B) across genes. r_half is averaged over the repeats (its sd
   is reported too); a repeat whose half means give a constant delta (no variance across genes) is dropped.
2. Spearman-Brown: the reliability of a mean over k times as many cells as one half is r_k = k r_half /
   (1 + (k - 1) r_half); with k = 2 this is the familiar r_full = 2 r_half / (1 + r_half), the reliability of
   the stored sample's mean delta, the share of its variance across genes that is signal rather than sampling
   noise. The recorded target may average more cells than were stored: a real bundle keeps at most a few
   hundred cells per perturbation for cell-eval while its target mean covers every cell of the perturbation,
   and a mean over more cells is more reliable. So the step is carried to the N cells behind the target,
   k = 2 N / n_stored: N = n_stored when the stored cells reproduce the recorded target (checked per
   perturbation), otherwise N is read from --ncells (a JSON file {perturbation: cells}, see below) and, without
   it, is unknown, k stays 2 and the ceiling of that perturbation is a lower bound; the report says so wherever
   a mean ceiling or a headroom is quoted. A perfect predictor of the true expected delta correlates with the
   observed target delta at sqrt(r_full): that is the ceiling of pearson_delta for p (clipped to [0, 1]; a
   non-positive r_half means the effect is not detectable at this sample size and the ceiling is reported as
   0). The ceiling of the averaged metric is the mean ceiling over the visible-validation perturbations; the
   median and range are reported beside it. A perturbation with fewer than 4 cells is skipped with a note.
3. Caveat: the control mean is shared by both halves, so its own sampling noise is common to A and B and
   inflates r_half slightly, most for weak effects. It is quantified by splitting the held-out control sample
   the same way: the correlation between the two half control means' deviations from the lab's control mean is
   the r_half a perturbation with no effect at all would show (shared control noise plus any systematic
   difference between the held-out and the public control cells); its Spearman-Brown ceiling is the "null
   ceiling". The ceiling is an upper bound under cell-sampling noise alone and ignores day and batch effects,
   which lower what any predictor can reach further but do not show in a within-sample split.
4. Optional --runs: for each run, the model the run selected (the best visible primary_score among the
   experiments the run scored on the sealed set at its end, as summary.json reports; if none, the best
   completed experiment) is re-scored on the visible validation set from its predictions.npz at its chosen
   alpha, per perturbation, and shown against the ceiling: a table, the Pearson correlation between achieved
   and ceiling across perturbations, and the mean achieved against the mean ceiling (the headroom). Only the
   visible labels are read.

    python tools/noise_ceiling.py --data data/adamson_cf --out docs/results/noise_ceiling.md --runs runs/a runs/b
    python tools/noise_ceiling.py --data data/adamson_cf --ncells data/adamson_cf/ncells.json --out ...
    python tools/noise_ceiling.py --from-json docs/results/noise_ceiling.json --out docs/results/noise_ceiling.md

The --ncells file maps each perturbation key to the number of cells its recorded target averages. A bundle
stores that count only for the training perturbations, so for the validation set it is produced from the raw
cells with the same grouping the ingest used (the manifest records the source file, condition_key,
control_value and collapse_by_target; genemila.data.real.parse_targets gives the key of a label), or the
bundle is re-ingested with max_eval_cells above the largest perturbation, after which every target is the
stored mean and no file is needed.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from genemila.benchmark.celleval import load_real_cells  # noqa: E402
from genemila.benchmark.evaluator import evaluate  # noqa: E402
from genemila.benchmark.table import run_arm  # noqa: E402
from genemila.data.bundle import LabelSet  # noqa: E402

VISIBLE = "val1"            # the visible validation part of a bundle
CONTROL = "control"         # label of the held-out control sample among the stored cells
MIN_CELLS = 4               # fewer cells cannot be split into two halves worth correlating
STORED_MEAN_TOL = 1e-3      # the stored cells are the whole population when their mean reproduces the target


def pearson(a: np.ndarray, b: np.ndarray) -> float:
    """Pearson correlation across genes; NaN when either vector is constant."""
    a = np.asarray(a, dtype=np.float64) - np.mean(a)
    b = np.asarray(b, dtype=np.float64) - np.mean(b)
    den = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / den) if den > 0 else float("nan")


def split_half_correlations(cells: np.ndarray, control_mean: np.ndarray, rng: np.random.Generator,
                            repeats: int) -> np.ndarray:
    """r_half of each random half split: Pearson across genes between the two halves' mean deltas from
    control_mean. cells: (n, genes) dense. NaN marks a degenerate repeat."""
    cells = np.asarray(cells, dtype=np.float64)
    n = cells.shape[0]
    out = np.empty(repeats)
    for i in range(repeats):
        perm = rng.permutation(n)
        a, b = perm[: n // 2], perm[n // 2:]
        out[i] = pearson(cells[a].mean(axis=0) - control_mean, cells[b].mean(axis=0) - control_mean)
    return out


def spearman_brown(r_half: float, k: float = 2.0) -> float:
    """Reliability of a mean over k times as many cells as one half (k = 2: the whole stored sample). Below
    r_half = -1 / (k - 1) the formula has no meaning (no signal at any sample size) and -1 is returned."""
    den = 1.0 + (k - 1.0) * r_half
    return k * r_half / den if den > 0 else -1.0


def ceiling_from(r_half: float, k: float = 2.0) -> tuple[float, float]:
    """(r_full, ceiling): the reliability of the target mean (k times one half) and sqrt of it clipped to [0, 1]."""
    r_full = spearman_brown(r_half, k)
    return r_full, float(np.sqrt(min(max(r_full, 0.0), 1.0)))


def _summ(values: np.ndarray) -> tuple[float | None, float | None, int]:
    """(mean, sd, number of finite values) of the finite entries."""
    v = np.asarray(values, dtype=np.float64)
    v = v[np.isfinite(v)]
    if v.size == 0:
        return None, None, 0
    return float(v.mean()), (float(v.std(ddof=1)) if v.size > 1 else 0.0), int(v.size)


def analyse_dataset(data_dir: Path, repeats: int = 50, seed: int = 0, ncells: dict[str, int] | None = None) -> dict:
    """Split-half reliability and ceiling of every visible-validation perturbation, plus the control caveat.
    ncells: cells behind each recorded target ({perturbation: N}); consulted only where the stored cells do not
    reproduce the target, and an entry below the stored count is an error."""
    data_dir = Path(data_dir).resolve()
    ncells = {str(k): int(v) for k, v in (ncells or {}).items()}
    manifest = json.loads((data_dir / "manifest.json").read_text()) if (data_dir / "manifest.json").exists() else {}
    z = np.load(data_dir / "public.npz", allow_pickle=False)
    public_control = z["control_cells"].astype(np.float64)
    control_mean = public_control.mean(axis=0)  # the vector the lab subtracts
    visible = LabelSet.load(data_dir / "private" / f"{VISIBLE}.npz")
    X, labels = load_real_cells(data_dir, VISIBLE)
    rng = np.random.default_rng(seed)
    rows, skipped = [], []
    for pert, target in zip(visible.perts, visible.means):
        idx = np.flatnonzero(labels == pert)
        n = int(idx.size)
        if n < MIN_CELLS:
            skipped.append({"pert": pert, "n_cells": n,
                            "reason": f"fewer than {MIN_CELLS} stored cells" if n else "no stored cells"})
            continue
        cells = X[idx].toarray()
        stored_mean = cells.astype(np.float64).mean(axis=0)
        rs = split_half_correlations(cells, control_mean, rng, repeats)
        r_mean, r_sd, n_valid = _summ(rs)
        if r_mean is None:
            skipped.append({"pert": pert, "n_cells": n, "reason": "constant delta in every split (no variance across genes)"})
            continue
        stored_is_target = bool(np.max(np.abs(stored_mean - target)) < STORED_MEAN_TOL)
        n_target = n if stored_is_target else ncells.get(pert)  # None: unknown, the ceiling is a lower bound
        if n_target is not None and n_target < n:
            raise ValueError(f"--ncells gives {n_target} cells for {pert} but {n} of its cells are stored")
        k = 2.0 * (n if n_target is None else n_target) / n
        r_full, ceiling = ceiling_from(r_mean, k)
        rows.append({"pert": pert, "n_cells": n, "n_target": n_target, "sb_k": k,
                     "r_half_mean": r_mean, "r_half_sd": r_sd, "valid_repeats": n_valid,
                     "r_full": r_full, "ceiling": ceiling, "target_is_stored_mean": stored_is_target})
    overall = None
    if rows:
        c = np.array([r["ceiling"] for r in rows])
        overall = {"n": len(rows), "mean_ceiling": float(c.mean()), "median_ceiling": float(np.median(c)),
                   "min_ceiling": float(c.min()), "max_ceiling": float(c.max()),
                   "mean_r_half": float(np.mean([r["r_half_mean"] for r in rows])),
                   "mean_r_full": float(np.mean([r["r_full"] for r in rows])),
                   "n_target_is_stored_mean": sum(1 for r in rows if r["target_is_stored_mean"]),
                   "n_corrected": sum(1 for r in rows if r["n_target"] is not None and r["n_target"] > r["n_cells"]),
                   "n_target_unknown": sum(1 for r in rows if r["n_target"] is None),
                   "lower_bound": any(r["n_target"] is None for r in rows),
                   "mean_cells": float(np.mean([r["n_cells"] for r in rows]))}
    control = None
    cidx = np.flatnonzero(labels == CONTROL)
    if cidx.size >= MIN_CELLS:
        rs = split_half_correlations(X[cidx].toarray(), control_mean, rng, repeats)
        r_mean, r_sd, n_valid = _summ(rs)
        null_r_full, null_ceiling = ceiling_from(r_mean) if r_mean is not None else (None, None)
        control = {"n_cells": int(cidx.size), "n_public_control_cells": int(public_control.shape[0]),
                   "r_half_mean": r_mean, "r_half_sd": r_sd, "valid_repeats": n_valid,
                   "null_r_full": null_r_full, "null_ceiling": null_ceiling}
    return {"tool": "noise_ceiling", "data_dir": str(data_dir), "dataset": manifest.get("name", data_dir.name),
            "split_id": manifest.get("split_id"), "n_genes": int(X.shape[1]),
            "n_public_control_cells": int(public_control.shape[0]), "n_visible": len(visible.perts),
            "repeats": int(repeats), "seed": int(seed), "ncells_file": None,
            "n_ncells_given": sum(1 for p in visible.perts if p in ncells),
            "perturbations": rows, "skipped": skipped, "overall": overall, "control": control, "runs": []}


def _selected_experiment(db) -> tuple[dict | None, str]:
    """The model the run selected: the best visible primary_score among the experiments it scored on the
    sealed set at its end (what summary.json reports), else the best completed experiment."""
    rows = db.query("SELECT experiment_id FROM experiments WHERE status='completed' AND primary_score IS NOT NULL "
                    "AND query_metrics_json IS NOT NULL AND COALESCE(kind, '') != 'ensemble' "
                    "ORDER BY primary_score DESC, finished_at ASC LIMIT 1")
    if rows:
        return db.get_experiment(rows[0]["experiment_id"]), "best visible score among the experiments scored on the sealed set"
    best = db.best()
    return best, "best completed experiment (none was scored on the sealed set)"


def analyse_run(run_dir: Path, dataset: dict) -> dict:
    """Achieved visible-validation pearson_delta per perturbation of the run's selected model, against the
    ceiling. Reads the run's predictions and the visible labels through the lab; the sealed set is never read."""
    from genemila.lab import open_run
    run_dir = Path(run_dir).resolve()
    cfg = json.loads((run_dir / "config.json").read_text()) if (run_dir / "config.json").exists() else {}
    summary = json.loads((run_dir / "summary.json").read_text()) if (run_dir / "summary.json").exists() else {}
    out = {"run_id": summary.get("run_id", run_dir.name), "dir": str(run_dir), "arm": run_arm(cfg, summary) if cfg else "unknown arm",
           "code": (summary.get("base_commit") or "")[:7], "workers": summary.get("workers") or (cfg.get("run") or {}).get("workers")}
    if not (run_dir / "lab.db").exists():  # re-opening would create an empty database in a directory that is no run
        return {**out, "error": "no lab.db in the run directory"}
    try:
        lab = open_run(run_dir)
    except Exception as exc:  # a run that cannot be re-opened is shown, not fatal
        return {**out, "error": f"{type(exc).__name__}: {exc}"[:300]}
    try:
        rec, how = _selected_experiment(lab.db)
        if rec is None:
            return {**out, "error": "no completed experiment"}
        pred, perts = lab._predict(rec, lab._val1.perts)
        if not perts:
            return {**out, "experiment_id": rec["experiment_id"], "selected_by": how,
                    "error": f"the predictions of {rec['experiment_id']} cover none of the visible validation perturbations"}
        truth = {p: m for p, m in zip(lab._val1.perts, lab._val1.means)}
        res = evaluate(pred, np.stack([truth[p] for p in perts]), lab.control_mean, perts)
        achieved = {p: res["per_perturbation"][p]["pearson_delta"] for p in perts}
        ceil = {r["pert"]: r for r in dataset["perturbations"]}
        table = [{"pert": p, "n_cells": ceil[p]["n_cells"], "n_target": ceil[p]["n_target"], "ceiling": ceil[p]["ceiling"],
                  "achieved": achieved[p], "gap": ceil[p]["ceiling"] - achieved[p]} for p in perts if p in ceil]
        note = None
        if lab.split_id != dataset.get("split_id"):
            note = (f"the run's split ({lab.split_id}) is not the dataset's ({dataset.get('split_id')}); "
                    f"{len(table)} of its {len(perts)} validation perturbations have a ceiling")
        elif len(table) < len(perts):
            note = f"{len(perts) - len(table)} validation perturbations have no ceiling (skipped above)"
        r = pearson([t["ceiling"] for t in table], [t["achieved"] for t in table]) if len(table) >= 3 else float("nan")
        mean_ach = float(np.mean([t["achieved"] for t in table])) if table else None
        mean_ceil = float(np.mean([t["ceiling"] for t in table])) if table else None
        out.update({
            "experiment_id": rec["experiment_id"], "selected_by": how, "kind": rec.get("kind"), "model": rec.get("model_type"),
            "features": rec.get("feature_set_json") or [], "best_alpha": rec.get("best_alpha"),
            "primary_score": rec.get("primary_score"),
            "recorded_pearson_delta": (rec.get("val_metrics_json") or {}).get("pearson_delta"),
            "pearson_delta_all_visible": res["metrics"]["pearson_delta"], "n_visible": len(perts),
            "split_id": lab.split_id, "per_perturbation": table, "n_matched": len(table),
            "mean_achieved": mean_ach, "mean_ceiling": mean_ceil,
            "headroom": None if mean_ach is None else mean_ceil - mean_ach,
            "ceiling_is_lower_bound": any(t["n_target"] is None for t in table),
            "achieved_vs_ceiling_r": None if not np.isfinite(r) else r, "note": note})
        return out
    except Exception as exc:  # missing or foreign artifacts, an incomplete record: shown, not fatal
        return {**out, "error": f"{type(exc).__name__}: {exc}"[:300]}
    finally:
        lab.close()


def _f(x, nd=3):
    return "n/a" if x is None else f"{x:.{nd}f}"


def _pm(mean, sd, nd=3):
    return "n/a" if mean is None else f"{mean:.{nd}f} ± {sd:.{nd}f}"


def render(rep: dict) -> str:
    R = rep["repeats"]
    L = [f"# Noise ceiling of pearson_delta on {rep['dataset']}", "",
         f"Visible data only: the {rep['n_visible']} visible-validation perturbations' held-out cells and the "
         f"{rep['n_public_control_cells']} public control cells (their mean is the lab's control_mean); the sealed set "
         f"is never read. For each perturbation its cells are split at random into two halves {R} times (seed "
         f"{rep['seed']}); r_half is the Pearson correlation across the {rep['n_genes']} genes between the two half-sample "
         "mean deltas from control_mean, averaged over the splits. Spearman-Brown gives the reliability of the "
         "recorded target's mean delta, r_full = k r_half / (1 + (k - 1) r_half) with k = 2 N / n_stored, where N is the "
         "number of cells the target averages (the stored cells themselves when their mean reproduces the target, "
         "else the count given with --ncells" + (f", here {rep['ncells_file']}" if rep.get("ncells_file") else "") +
         "; unknown without it, in which case k = 2 and the ceiling is a lower bound). sqrt(r_full) is the correlation "
         "a perfect predictor of the true expected delta would reach against the recorded target: the ceiling of "
         "pearson_delta for that perturbation (clipped to [0, 1]). The ceiling of the averaged metric is the mean over "
         f"perturbations. Perturbations with fewer than {MIN_CELLS} cells are skipped.", "",
         "## Per perturbation (visible validation set)", "",
         f"| perturbation | stored cells | target cells | r_half (mean ± sd over {R} splits) | r_full (Spearman-Brown) | ceiling |",
         "|---|---|---|---|---|---|"]
    for r in rep["perturbations"]:
        n_target = "unknown (lower bound)" if r["n_target"] is None else str(r["n_target"])
        L.append(f"| {r['pert']} | {r['n_cells']} | {n_target} | {_pm(r['r_half_mean'], r['r_half_sd'])} | {_f(r['r_full'])} | {_f(r['ceiling'])} |")
    if rep["skipped"]:
        L += ["", "Skipped: " + "; ".join(f"{s['pert']} ({s['n_cells']} cells: {s['reason']})" for s in rep["skipped"]) + "."]
    ov = rep["overall"]
    L += ["", "## Overall", ""]
    if ov:
        L += [f"- Mean ceiling over the {ov['n']} visible-validation perturbations: **{ov['mean_ceiling']:.3f}** (the ceiling of "
              f"the averaged metric); median {ov['median_ceiling']:.3f}; range {ov['min_ceiling']:.3f} to {ov['max_ceiling']:.3f}.",
              f"- Mean r_half {ov['mean_r_half']:.3f}, mean r_full {ov['mean_r_full']:.3f}; {ov['mean_cells']:.0f} stored cells per "
              f"perturbation on average.",
              f"- The stored cells are the whole population behind the recorded target mean for {ov['n_target_is_stored_mean']} of "
              f"{ov['n']} perturbations" + (
                  "." if ov["n_target_is_stored_mean"] == ov["n"] else
                  f"; for the other {ov['n'] - ov['n_target_is_stored_mean']} the recorded target averages more cells than were "
                  "stored and its sampling noise is smaller" + (
                      f". The Spearman-Brown step was carried to the cell count behind the target (--ncells) for {ov['n_corrected']}"
                      " of them" if ov["n_corrected"] else "") + (
                      f"; for {ov['n_target_unknown']} the count is unknown, so their ceiling is a lower bound, and so are the "
                      "mean ceiling and every headroom below (pass --ncells to correct it)." if ov["n_target_unknown"] else "."))]
    else:
        L.append("No visible-validation perturbation had enough stored cells.")
    L += ["", "## Control-noise caveat", ""]
    c = rep["control"]
    if c:
        L += [f"- Both halves subtract the same control_mean (the mean of {c['n_public_control_cells']} public control cells), so "
              "its sampling noise is common to A and B and inflates r_half slightly, most for weak effects.",
              f"- Splitting the {c['n_cells']} held-out control cells the same way, the correlation between the two half control "
              f"means' deviations from control_mean is {_pm(c['r_half_mean'], c['r_half_sd'])} (r_full {_f(c['null_r_full'])}, "
              f"null ceiling {_f(c['null_ceiling'])}): the r_half a perturbation with no effect would show from the shared control "
              "mean alone, plus any systematic difference between the held-out and the public control cells. r_half values "
              "near it are not evidence of a reproducible response."]
        if c["r_half_mean"] is not None and c["r_half_mean"] < 0:
            L.append("- A negative value means the held-out control sample overlaps the public control cells (the synthetic "
                     "generator draws both from one pool), which turns the shared term negative; a real bundle keeps the "
                     "two samples disjoint and the value is then small and positive.")
    else:
        L.append("The bundle stores no held-out control sample, so the shared-control inflation could not be quantified.")
    runs = rep.get("runs") or []
    if runs:
        L += ["", "## Achieved vs ceiling", "",
              "The run's selected model re-scored on the visible validation set (pearson_delta per perturbation from its "
              "predictions at its chosen alpha, against the recorded target means) next to the ceiling. The gap is ceiling "
              "minus achieved; cells are the stored cells."]
        L += ["", "| run | arm | selected | mean achieved | headroom | r(achieved, ceiling) |", "|---|---|---|---|---|---|"]
        for run in runs:
            if run.get("error"):
                L.append(f"| {run['run_id']} | {run['arm']} | Not scored: {run['error']} | | | |")
                continue
            lb = "at least " if run.get("ceiling_is_lower_bound") else ""
            ach = f"{run['mean_achieved']:.3f}" if run["n_matched"] else ""
            head = f"{lb}{run['headroom']:+.3f}" if run["n_matched"] else ""
            L.append(f"| {run['run_id']} | {run['arm']} | {run['experiment_id']}, alpha {run['best_alpha']} | {ach} | "
                     f"{head} | {_f(run['achieved_vs_ceiling_r'])} |")
        scored_runs = [r for r in runs if not r.get("error") and r["n_matched"]]
        if scored_runs:
            top = max(scored_runs, key=lambda r: r["mean_achieved"])
            feats = ", ".join(top["features"][:6]) + (", ..." if len(top["features"]) > 6 else "")
            L += ["", f"### Per perturbation, for the run with the highest mean achieved: {top['run_id']}", "",
                  f"Selected model {top['experiment_id']} ({top['selected_by']}): {top['model']} on {feats or 'no features'}, "
                  f"alpha {top['best_alpha']}; {top['arm']}, code {top['code'] or '?'}. Every run's per-perturbation values "
                  "are in the JSON twin."]
            if top.get("note"):
                L.append(f"Note: {top['note']}.")
            L += ["", "| perturbation | cells | ceiling | achieved | gap |", "|---|---|---|---|---|"]
            for t in top["per_perturbation"]:
                L.append(f"| {t['pert']} | {t['n_cells']} | {_f(t['ceiling'])} | {_f(t['achieved'])} | {t['gap']:+.3f} |")
    L += ["", "## Reading", ""]
    if ov:
        spread = (f"(median {ov['median_ceiling']:.3f}, range {ov['min_ceiling']:.3f} to {ov['max_ceiling']:.3f} across "
                  "perturbations)")
        if ov.get("lower_bound"):
            head = (f"Under cell-sampling noise alone, pearson_delta on this visible validation set can reach at least about "
                    f"{ov['mean_ceiling']:.3f} on average {spread}. This is a lower bound on the ceiling, not the ceiling: for "
                    f"{ov['n_target_unknown']} of {ov['n']} perturbations the recorded target averages more cells than were "
                    "stored and their count was not given, so their reliability is that of the smaller stored sample; pass "
                    "--ncells with the cell counts to carry the Spearman-Brown step to the target and the headroom below is "
                    "understated until then.")
        else:
            head = (f"Under cell-sampling noise alone, pearson_delta on this visible validation set cannot exceed about "
                    f"{ov['mean_ceiling']:.3f} on average {spread}.")
            if ov.get("n_corrected"):
                head += (f" For {ov['n_corrected']} perturbations the target averages more cells than were stored and the "
                         "Spearman-Brown step was carried to that count.")
        lb = "at least " if ov.get("lower_bound") else ""
        scored = [r for r in runs if not r.get("error") and r["n_matched"]]
        if scored:
            ach = [r["mean_achieved"] for r in scored]
            hd = [r["headroom"] for r in scored]
            if len(scored) == 1:
                head += (f" The run's selected model reaches {ach[0]:.3f} on these perturbations, leaving {lb}{hd[0]:+.3f} "
                         "between it and the noise ceiling.")
            else:
                head += (f" The {len(scored)} runs' selected models reach {min(ach):.3f} to {max(ach):.3f} on these "
                         f"perturbations, leaving {lb}{min(hd):+.3f} to {lb}{max(hd):+.3f} between them and the noise ceiling.")
            head += (" That gap bounds what a predictor that knew each target's true response could add; a predictor "
                     "limited to the information in the bundle (the other perturbations' responses and the knowledge "
                     "files) is bounded by what that information says about a new target, which can lie well below.")
            tc = rep.get("transfer_ceiling")
            if tc:
                head += (f" On the training perturbations, the best hindsight mix of the other perturbations' responses "
                         f"reaches {tc['nonneg']:.3f} (non-negative weights) to {tc['any_linear']:.3f} (any linear weights) "
                         f"({tc['source']}), so the part of the gap above that needs new information about the targets "
                         "themselves, not better modelling of the same information.")
            head += (" Where achieved tracks the ceiling across perturbations (a high correlation in the table), the "
                     "perturbations the models miss are also the ones whose response is least reproducible.")
        L.append(head + " The ceiling is an estimate under cell-sampling noise alone: it treats the recorded target as the "
                 "true expected response plus the noise of n cells, it is inflated slightly by the shared control mean (the "
                 "null ceiling above says by how much a null perturbation would score), and it ignores day and batch effects, "
                 "which lower what any predictor can reach but do not show in a within-sample split. It is an upper bound "
                 "on the visible validation set, not a prediction for the sealed set.")
    else:
        L.append("No ceiling could be estimated: no visible-validation perturbation had enough stored cells.")
    return "\n".join(L) + "\n"


def _clean(obj):
    """JSON-safe copy: NaN and infinities become null so the twin re-renders exactly."""
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_clean(v) for v in obj]
    if isinstance(obj, (np.floating, float)):
        return None if not np.isfinite(obj) else float(obj)
    if isinstance(obj, np.integer):
        return int(obj)
    return obj


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--data", help="dataset bundle directory (public.npz, manifest.json, held-out cells)")
    ap.add_argument("--out", required=True, help="markdown report; a .json twin is written next to it unless --json is given")
    ap.add_argument("--json", default=None, help="where to write the JSON twin (default: --out with .json)")
    ap.add_argument("--runs", nargs="*", default=[], help="run directories: show each run's selected model against the ceiling")
    ap.add_argument("--repeats", type=int, default=50, help="random half splits per perturbation (default 50)")
    ap.add_argument("--seed", type=int, default=0, help="seed of the splits (default 0)")
    ap.add_argument("--ncells", default=None, help="JSON {perturbation: cells} with the number of cells each recorded "
                    "target averages, for perturbations whose stored cells are a subsample (see the module docstring)")
    ap.add_argument("--transfer-ceiling", default=None, help="ceiling_analysis.json from tools/ceiling_analysis.py: quote its "
                    "hindsight transfer ceilings in the Reading")
    ap.add_argument("--from-json", default=None, help="re-render the markdown from an earlier JSON twin (no data is read)")
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    if args.from_json:
        rep = json.loads(Path(args.from_json).read_text())
        md = render(rep)
        out.write_text(md)
        print(md)
        return 0
    if not args.data:
        ap.error("--data is required unless --from-json is given")
    if args.repeats < 1:
        ap.error("--repeats must be at least 1")
    ncells = json.loads(Path(args.ncells).read_text()) if args.ncells else None
    if ncells is not None and not (isinstance(ncells, dict) and all(isinstance(v, int) and v > 0 for v in ncells.values())):
        ap.error("--ncells must be a JSON object mapping perturbation to a positive integer cell count")
    rep = analyse_dataset(Path(args.data), repeats=args.repeats, seed=args.seed, ncells=ncells)
    rep["ncells_file"] = args.ncells
    rep["runs"] = [analyse_run(Path(d), rep) for d in args.runs]
    if args.transfer_ceiling:
        tc = json.loads(Path(args.transfer_ceiling).read_text())
        rep["transfer_ceiling"] = {"nonneg": float(tc["oracle_nonneg_combination"]),
                                   "any_linear": float(tc["oracle_any_linear_combination"]),
                                   "source": Path(args.transfer_ceiling).name}
    rep = _clean(rep)
    md = render(rep)
    out.write_text(md)
    Path(args.json or out.with_suffix(".json")).write_text(json.dumps(rep, indent=1, default=str))
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
