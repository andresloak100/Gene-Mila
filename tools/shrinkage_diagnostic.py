"""Fixed, nested development-only additive-ridge magnitude diagnostic.

Uses public training labels, never the bundle's private data, splits, or oracle.
See docs/NORMAN_SHRINKAGE_PLAN.md before any real run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from genemila.benchmark.comparable import cellforge  # noqa: E402
from genemila.benchmark.evaluator import _pearson, evaluate  # noqa: E402
from genemila.features.api import FeatureContext  # noqa: E402
from genemila.features.builtin import (  # noqa: E402
    AdditiveResponse, ControlMean, IsTarget, MeanResponse, additive_delta,
)
from genemila.pipeline import cv_folds_of, make_model  # noqa: E402

ALPHAS = (0.01, 1.0, 100.0, 10000.0, 1000000.0)
LOW_ALPHAS = ALPHAS[:3]
SEEDS = (0, 1, 2)
OUTER_FOLDS = 5
INNER_FOLDS = 3
FEATURE_CLASSES = (ControlMean, MeanResponse, IsTarget, AdditiveResponse)
FEATURES = tuple(cls.name for cls in FEATURE_CLASSES)
RECIPES = ("additive", "ridge", "ridge_low_penalty", "ridge_calibrated")
METRICS = (
    "pearson_delta", "mse", "pearson_expr", "cellforge_r2", "mse_top",
    "cellforge_pcc_de", "r2_top", "pearson_delta_top", "direction_acc_top",
    "delta_scale_ratio",
)


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _order_hash(values: list[str]) -> str:
    return hashlib.sha256(json.dumps(values, ensure_ascii=False).encode()).hexdigest()


def fixed_config(public: Path, ctx: FeatureContext) -> dict:
    """Fingerprint only the explicitly allowed public inputs and source/protocol."""
    import sklearn
    source_paths = (
        "tools/shrinkage_diagnostic.py", "docs/NORMAN_SHRINKAGE_PLAN.md",
        "genemila/features/api.py", "genemila/features/builtin.py",
        "genemila/pipeline.py", "genemila/benchmark/evaluator.py",
        "genemila/benchmark/comparable.py", "genemila/benchmark/__init__.py",
    )
    manifest = json.loads((public / "manifest.json").read_text())
    return {
        "schema_version": 1, "status": "fixed_before_fitting", "public_dir": str(public),
        "dataset": manifest.get("name"), "split_id": manifest.get("split_id"),
        "label_scope": "public training only; nested development folds",
        "features": list(FEATURES), "alphas": list(ALPHAS), "low_alphas": list(LOW_ALPHAS),
        "outer_seeds": list(SEEDS), "outer_folds": OUTER_FOLDS, "inner_folds": INNER_FOLDS,
        "inner_seed_rule": "1000 + 100 * outer_seed + outer_fold_index",
        "alpha_selection": "inner OOF mean Pearson delta; smaller alpha wins exact ties",
        "calibration": "through-origin LS on selected-alpha inner OOF deltas; clip [0,4]; zero denominator ->1",
        "recipes": list(RECIPES), "metrics": list(METRICS),
        "top_genes": "20 highest absolute true development delta; no cell-derived reference",
        "n_train": len(ctx.train_perts), "n_genes": ctx.n_genes,
        "train_order_sha256": _order_hash(ctx.train_perts), "gene_order_sha256": _order_hash(ctx.genes),
        "input_sha256": {name: _hash(public / name) for name in
                         ("public.npz", "knowledge/targets.json", "manifest.json")},
        "source_sha256": {name: _hash(REPO / name) for name in source_paths},
        "versions": {"python": platform.python_version(), "numpy": np.__version__,
                     "scikit_learn": sklearn.__version__},
        "max_ridge_fits": 255, "api_cost_usd": 0,
        "interpretation": "exploratory development diagnostic; seed SD is fold sensitivity, not independent replication",
    }


def _check_context(ctx: FeatureContext) -> None:
    if len(ctx.train_perts) < 3 or len(set(ctx.train_perts)) != len(ctx.train_perts):
        raise ValueError("training views require at least three distinct perturbations")
    if ctx.n_genes < 2 or len(set(ctx.genes)) != ctx.n_genes:
        raise ValueError("at least two distinct genes are required")
    _, truth = ctx.train_delta()
    if truth.shape != (len(ctx.train_perts), ctx.n_genes) or not np.all(np.isfinite(truth)):
        raise ValueError("public training deltas have invalid shape or nonfinite values")
    if ctx.control_mean.shape != (ctx.n_genes,) or not np.all(np.isfinite(ctx.control_mean)):
        raise ValueError("control mean has invalid shape or nonfinite values")


def _folds(ctx: FeatureContext, count: int, seed: int):
    _check_context(ctx)
    targets = {p: ctx.target_genes(p) for p in ctx.train_perts}
    folds = cv_folds_of(ctx.train_perts, count, seed, targets)
    if len(folds) != count:
        raise ValueError("too few nonempty gene-grouped folds for the fixed protocol")
    predicted = [p for predict, _ in folds for p in predict]
    if sorted(predicted) != sorted(ctx.train_perts):
        raise ValueError("development folds do not partition the training perturbations")
    for predict, hide in folds:
        if not predict or not set(predict).issubset(hide):
            raise ValueError("invalid gene-grouped fold")
        _check_context(ctx.without_train(hide))
    return folds


def _matrix(ctx: FeatureContext, perts: list[str]) -> np.ndarray:
    """Known built-ins only, recomputed under this view without registry/plugin caches."""
    blocks = [np.asarray(cls().compute(ctx, perts, {}), dtype=np.float64) for cls in FEATURE_CLASSES]
    if any(block.shape != (len(perts), ctx.n_genes, 1) for block in blocks):
        raise ValueError("built-in feature shape changed")
    x = np.concatenate(blocks, axis=2).reshape(len(perts) * ctx.n_genes, len(FEATURES))
    if not np.all(np.isfinite(x)):
        raise ValueError("built-in feature matrix contains nonfinite values")
    return x


def _fit_predictions(ctx: FeatureContext, perts: list[str], alphas: tuple[float, ...], seed: int):
    """Standardization, features and fit see exactly this training view's labels."""
    _check_context(ctx)
    if set(perts).intersection(ctx.train_perts):
        raise ValueError("scored fold perturbations remain in the fitting view")
    both = ctx.train_perts + perts
    x = _matrix(ctx, both)
    n_rows = len(ctx.train_perts) * ctx.n_genes
    train_x, pred_x = x[:n_rows], x[n_rows:]
    mu, sd = train_x.mean(axis=0), train_x.std(axis=0)
    sd[sd == 0] = 1.0
    train_x, pred_x = (train_x - mu) / sd, (pred_x - mu) / sd
    _, d = ctx.train_delta()
    out = {}
    for alpha in alphas:
        model = make_model("ridge", alpha, seed)
        model.fit(train_x, d.reshape(-1))
        pred = model.predict(pred_x).reshape(len(perts), ctx.n_genes)
        if not np.all(np.isfinite(pred)):
            raise ValueError("ridge produced nonfinite predictions")
        out[alpha] = pred
    return out


def _pearson_delta(pred: np.ndarray, truth: np.ndarray) -> float:
    # Same protected definition as the lab, including zero correlations.
    return float(np.mean([_pearson(p, d) for p, d in zip(pred, truth)]))


def _calibration(pred: np.ndarray, truth: np.ndarray) -> dict:
    denominator = float(np.sum(pred * pred))
    numerator = float(np.sum(pred * truth))
    if not np.isfinite(denominator) or not np.isfinite(numerator):
        raise ValueError("nonfinite calibration statistics")
    raw = numerator / denominator if denominator > 0 else 1.0
    if not np.isfinite(raw):
        raise ValueError("nonfinite calibration scalar")
    return {"scale": float(np.clip(raw, 0.0, 4.0)), "unclipped_scale": raw,
            "zero_denominator": denominator == 0}


def fit_outer(ctx: FeatureContext, predict: list[str], hide: list[str], seed: int, fold_index: int):
    """Return outer predictions and fit metadata; never accesses the outer response rows."""
    view = ctx.without_train(hide)
    _check_context(view)
    if not set(predict).issubset(hide):
        raise ValueError("outer predictions must belong to the hidden set")
    inner_seed = 1000 + 100 * seed + fold_index
    pos = {p: i for i, p in enumerate(view.train_perts)}
    oof = {alpha: np.zeros((len(view.train_perts), view.n_genes)) for alpha in ALPHAS}
    inner_memberships = []
    for fold, inner_hide in _folds(view, INNER_FOLDS, inner_seed):
        inner_view = view.without_train(inner_hide)
        predictions = _fit_predictions(inner_view, fold, ALPHAS, inner_seed)
        rows = [pos[p] for p in fold]
        for alpha in ALPHAS:
            oof[alpha][rows] = predictions[alpha]
        inner_memberships.append({"predict": fold, "hide": inner_hide, "train": inner_view.train_perts})
    _, inner_truth = view.train_delta()
    scores = {alpha: _pearson_delta(oof[alpha], inner_truth) for alpha in ALPHAS}
    if not all(np.isfinite(score) for score in scores.values()):
        raise ValueError("nonfinite inner selection score")
    alpha = max(ALPHAS, key=lambda a: (scores[a], -a))
    low_alpha = max(LOW_ALPHAS, key=lambda a: (scores[a], -a))
    calibration = _calibration(oof[alpha], inner_truth)
    final = _fit_predictions(view, predict, tuple(dict.fromkeys((alpha, low_alpha))), seed)
    _, train_d = view.train_delta()
    additive = additive_delta(predict, {p: ctx.target_genes(p) for p in
                              [*view.train_perts, *predict]}, view.train_perts, train_d)
    out = {"additive": additive, "ridge": final[alpha], "ridge_low_penalty": final[low_alpha],
           "ridge_calibrated": final[alpha] * calibration["scale"]}
    if any(not np.all(np.isfinite(v)) for v in out.values()):
        raise ValueError("nonfinite outer predictions")
    meta = {"fold_index": fold_index, "inner_seed": inner_seed,
            "predict": predict, "hide": hide, "train": view.train_perts,
            "inner_folds": inner_memberships, "alpha": alpha, "low_alpha": low_alpha,
            "inner_selection_scores": {str(a): scores[a] for a in ALPHAS}, "calibration": calibration}
    return out, meta


def score_development(pred_delta: np.ndarray, truth_delta: np.ndarray, control: np.ndarray,
                      perts: list[str]) -> dict:
    pred, truth = pred_delta + control, truth_delta + control
    metrics = evaluate(pred, truth, control, perts)["metrics"]
    top = np.argsort(-np.abs(truth_delta), axis=1)[:, :20]
    comparable = cellforge(pred, truth, top)
    metrics.update(comparable)
    denominator = float(np.mean(np.abs(truth_delta)))
    metrics["delta_scale_ratio"] = float(np.mean(np.abs(pred_delta)) / max(1e-12, denominator))
    out = {key: float(metrics[key]) for key in METRICS}
    if not all(np.isfinite(v) for v in out.values()):
        raise ValueError("nonfinite development metrics")
    return out


def _mean_sd(values: list[float]) -> dict:
    return {"mean": float(np.mean(values)), "sd": float(np.std(values, ddof=1)), "n_seeds": len(values)}


def diagnose(ctx: FeatureContext) -> dict:
    _check_context(ctx)
    perts = list(ctx.train_perts)
    pos = {p: i for i, p in enumerate(perts)}
    repeats = []
    for seed in SEEDS:
        predictions = {recipe: np.zeros((len(perts), ctx.n_genes)) for recipe in RECIPES}
        fold_metadata = []
        for index, (fold, hide) in enumerate(_folds(ctx, OUTER_FOLDS, seed)):
            pred, meta = fit_outer(ctx, fold, hide, seed, index)
            rows = [pos[p] for p in fold]
            for recipe in RECIPES:
                predictions[recipe][rows] = pred[recipe]
            fold_metadata.append(meta)
        # Full public training responses are accessed here only for scoring frozen outer predictions.
        _, truth = ctx.train_delta()
        repeats.append({"seed": seed, "folds": fold_metadata,
                        "metrics": {r: score_development(predictions[r], truth, ctx.control_mean, perts)
                                    for r in RECIPES}})
    aggregate = {r: {m: _mean_sd([row["metrics"][r][m] for row in repeats]) for m in METRICS}
                 for r in RECIPES}
    differences = {reference: {r: {m: _mean_sd([row["metrics"][r][m] - row["metrics"][reference][m]
                                             for row in repeats]) for m in METRICS}
                              for r in RECIPES if r != reference}
                   for reference in ("additive", "ridge")}
    return {"schema_version": 1, "status": "complete", "label_scope": "public training development only",
            "n_train": len(perts), "n_genes": ctx.n_genes, "scored_training_perturbations": perts,
            "repeats": repeats, "mean_sd_over_seeds": aggregate, "paired_differences_over_seeds": differences,
            "uncertainty": "sample SD over fold seeds; same cohort reused, no independent replication or significance claim",
            "selection": "none; all fixed recipes reported; delivered B1 model unchanged"}


def run(public: Path, out: Path) -> dict:
    public, out = public.resolve(), out.resolve()
    if out == public or public in out.parents:
        raise ValueError("output must not be inside the input bundle")
    # Do not modify or inspect an existing run, even if it is incomplete.
    out.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    try:
        ctx = FeatureContext(public)
        config = fixed_config(public, ctx)
        (out / "config.json").write_text(json.dumps(config, indent=2, allow_nan=False) + "\n")
        summary = diagnose(ctx)
        summary["elapsed_s"] = time.monotonic() - start
        summary["config_sha256"] = _hash(out / "config.json")
        summary["run_directory"] = str(out)
        (out / "summary.json").write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n")
        return summary
    except Exception:
        (out / "FAILED.txt").write_text("Diagnostic failed; preserve this directory and inspect the invoking process error.\n")
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--public", type=Path, required=True, help="directory with public.npz and public knowledge")
    parser.add_argument("--out", type=Path, required=True, help="new exclusive output directory")
    args = parser.parse_args(argv)
    summary = run(args.public, args.out)
    print(json.dumps({"run_directory": summary["run_directory"], "status": summary["status"],
                      "mean_sd_over_seeds": summary["mean_sd_over_seeds"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
