#!/usr/bin/env python3
"""How high can pearson_delta go on a dataset? A noise ceiling from cell-sampling noise, on visible data only.

pearson_delta scores a prediction against the mean expression of a finite sample of perturbed cells. That mean
is the true expected response plus the sampling noise of n cells, so even a predictor that knew the true
response exactly would not reach a correlation of 1: the metric has a ceiling set by the data, and the gap
between a run's score and that ceiling is the headroom that modelling can still close. The ceiling is
estimated here from the visible validation perturbations' held-out cells and the public control cells (the
same vector the lab subtracts as control_mean). The sealed set is never touched.

Method, per visible-validation perturbation p with n cells, repeated R times with a fixed seed:

1. Split its cells at random into two halves A and B. delta_A = mean(A) - control_mean and delta_B = mean(B) -
   control_mean; r_half = Pearson(delta_A, delta_B) across genes. r_half is averaged over the repeats (its sd
   is reported too); a repeat whose half means give a constant delta (no variance across genes) is dropped.
2. Spearman-Brown: r_full = 2 r_half / (1 + r_half) is the reliability of the full-sample mean delta, the share
   of its variance across genes that is signal rather than sampling noise. A perfect predictor of the true
   expected delta correlates with the observed full-sample delta at sqrt(r_full): that is the ceiling of
   pearson_delta for p (clipped to [0, 1]; a negative r_half means the effect is not detectable at this sample
   size and the ceiling is reported as 0). The ceiling of the averaged metric is the mean ceiling over the
   visible-validation perturbations; the median and range are reported beside it. A perturbation with fewer
   than 4 cells is skipped with a note.
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
    python tools/noise_ceiling.py --from-json docs/results/noise_ceiling.json --out docs/results/noise_ceiling.md
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


def spearman_brown(r_half: float) -> float:
    """Reliability of a sample twice the size of each half (the full sample)."""
    return 2.0 * r_half / (1.0 + r_half) if r_half > -1.0 else -1.0


def ceiling_from(r_half: float) -> tuple[float, float]:
    """(r_full, ceiling): the full-sample reliability and sqrt of it clipped to [0, 1]."""
    r_full = spearman_brown(r_half)
    return r_full, float(np.sqrt(min(max(r_full, 0.0), 1.0)))


def _summ(values: np.ndarray) -> tuple[float | None, float | None, int]:
    """(mean, sd, number of finite values) of the finite entries."""
    v = np.asarray(values, dtype=np.float64)
    v = v[np.isfinite(v)]
    if v.size == 0:
        return None, None, 0
    return float(v.mean()), (float(v.std(ddof=1)) if v.size > 1 else 0.0), int(v.size)


def analyse_dataset(data_dir: Path, repeats: int = 50, seed: int = 0) -> dict:
    """Split-half reliability and ceiling of every visible-validation perturbation, plus the control caveat."""
    data_dir = Path(data_dir).resolve()
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
        r_full, ceiling = ceiling_from(r_mean)
        rows.append({"pert": pert, "n_cells": n, "r_half_mean": r_mean, "r_half_sd": r_sd, "valid_repeats": n_valid,
                     "r_full": r_full, "ceiling": ceiling,
                     "target_is_stored_mean": bool(np.max(np.abs(stored_mean - target)) < STORED_MEAN_TOL)})
    overall = None
    if rows:
        c = np.array([r["ceiling"] for r in rows])
        overall = {"n": len(rows), "mean_ceiling": float(c.mean()), "median_ceiling": float(np.median(c)),
                   "min_ceiling": float(c.min()), "max_ceiling": float(c.max()),
                   "mean_r_half": float(np.mean([r["r_half_mean"] for r in rows])),
                   "mean_r_full": float(np.mean([r["r_full"] for r in rows])),
                   "n_target_is_stored_mean": sum(1 for r in rows if r["target_is_stored_mean"]),
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
            "repeats": int(repeats), "seed": int(seed), "perturbations": rows, "skipped": skipped,
            "overall": overall, "control": control, "runs": []}


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
        truth = {p: m for p, m in zip(lab._val1.perts, lab._val1.means)}
        res = evaluate(pred, np.stack([truth[p] for p in perts]), lab.control_mean, perts)
        achieved = {p: res["per_perturbation"][p]["pearson_delta"] for p in perts}
        ceil = {r["pert"]: r for r in dataset["perturbations"]}
        table = [{"pert": p, "n_cells": ceil[p]["n_cells"], "ceiling": ceil[p]["ceiling"], "achieved": achieved[p],
                  "gap": ceil[p]["ceiling"] - achieved[p]} for p in perts if p in ceil]
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
            "achieved_vs_ceiling_r": None if not np.isfinite(r) else r, "note": note})
        return out
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
         "full-sample mean delta, r_full = 2 r_half / (1 + r_half), and sqrt(r_full) is the correlation a perfect "
         "predictor of the true expected delta would reach against the recorded target: the ceiling of pearson_delta "
         "for that perturbation (clipped to [0, 1]). The ceiling of the averaged metric is the mean over "
         f"perturbations. Perturbations with fewer than {MIN_CELLS} cells are skipped.", "",
         "## Per perturbation (visible validation set)", "",
         f"| perturbation | cells | r_half (mean ± sd over {R} splits) | r_full (Spearman-Brown) | ceiling |",
         "|---|---|---|---|---|"]
    for r in rep["perturbations"]:
        L.append(f"| {r['pert']} | {r['n_cells']} | {_pm(r['r_half_mean'], r['r_half_sd'])} | {_f(r['r_full'])} | {_f(r['ceiling'])} |")
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
                  "; for the others the recorded target averages more cells than were stored, its sampling noise is smaller, "
                  "and the true ceiling is at or above the value shown.")]
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
              "minus achieved."]
        for run in runs:
            L += ["", f"### {run['run_id']}: {run['arm']}, {run['workers']} workers, code {run['code'] or '?'}", ""]
            if run.get("error"):
                L.append(f"Not scored: {run['error']}.")
                continue
            feats = ", ".join(run["features"][:6]) + (", ..." if len(run["features"]) > 6 else "")
            L += [f"Selected model {run['experiment_id']} ({run['selected_by']}): {run['model']} on {feats or 'no features'}, "
                  f"alpha {run['best_alpha']}, visible selection score {_f(run['primary_score'], 4)}, recorded validation "
                  f"pearson_delta {_f(run['recorded_pearson_delta'], 4)}, re-scored {_f(run['pearson_delta_all_visible'], 4)} "
                  f"over {run['n_visible']} validation perturbations."]
            if run.get("note"):
                L.append(f"Note: {run['note']}.")
            L += ["", "| perturbation | cells | ceiling | achieved | gap |", "|---|---|---|---|---|"]
            for t in run["per_perturbation"]:
                L.append(f"| {t['pert']} | {t['n_cells']} | {_f(t['ceiling'])} | {_f(t['achieved'])} | {t['gap']:+.3f} |")
            if run["n_matched"]:
                L += ["", f"Mean achieved {run['mean_achieved']:.3f} vs mean ceiling {run['mean_ceiling']:.3f} over {run['n_matched']} "
                      f"perturbations: headroom {run['headroom']:+.3f}. Pearson correlation between achieved and ceiling across "
                      f"perturbations: {_f(run['achieved_vs_ceiling_r'])}" + (
                          "" if run["achieved_vs_ceiling_r"] is not None else " (fewer than 3 perturbations)") + "."]
    L += ["", "## Reading", ""]
    if ov:
        head = (f"Under cell-sampling noise alone, pearson_delta on this visible validation set cannot exceed about "
                f"{ov['mean_ceiling']:.3f} on average (median {ov['median_ceiling']:.3f}, range {ov['min_ceiling']:.3f} to "
                f"{ov['max_ceiling']:.3f} across perturbations).")
        scored = [r for r in runs if not r.get("error") and r["n_matched"]]
        if scored:
            parts = [f"{r['run_id']} reaches {r['mean_achieved']:.3f}, leaving {r['headroom']:+.3f}" for r in scored]
            head += (" " + "; ".join(parts) + " of headroom (mean ceiling minus mean achieved over the matched perturbations). "
                     "A gap of this size is what modelling can still close on these perturbations; a gap near zero means the "
                     "metric is saturated by the data and further gains must come from the sealed set's own noise, not from "
                     "the model. Where achieved tracks the ceiling across perturbations (a high correlation in the tables), "
                     "the perturbations the model misses are also the ones whose response is least reproducible.")
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
    rep = analyse_dataset(Path(args.data), repeats=args.repeats, seed=args.seed)
    rep["runs"] = [analyse_run(Path(d), rep) for d in args.runs]
    rep = _clean(rep)
    md = render(rep)
    out.write_text(md)
    Path(args.json or out.with_suffix(".json")).write_text(json.dumps(rep, indent=1, default=str))
    print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
