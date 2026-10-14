"""Fixed B1 recipe diagnosis on public-training gene folds only.

Read docs/B1_DIAGNOSTIC_PLAN.md before fitting. No search, new candidate,
private responses, split files, oracle, or API provider is used here.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import platform
import signal
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from genemila.benchmark.comparable import cellforge  # noqa: E402
from genemila.benchmark.evaluator import evaluate  # noqa: E402
from genemila.features.api import FeatureContext  # noqa: E402
from genemila.features.builtin import AdditiveResponse  # noqa: E402
from genemila.frozen import _plugins, load_export  # noqa: E402
from genemila.pipeline import build_matrix, cv_folds_of, make_model  # noqa: E402

MANIFEST_SHA256 = "225adc3079251f3cd17f16999b3bc92ab18ae20e9fcde9ee0617b8f350869b45"
SEEDS, OUTER_FOLDS, MAX_FITS, MAX_SECONDS = (0, 1, 2), 5, 45, 7200
KNOWLEDGE = "replogle2022_k562"
RECIPES = ("ensemble", "member_0", "member_1", "member_2", "additive")
METRICS = ("pearson_delta", "mse", "pearson_expr", "cellforge_r2", "mse_top",
           "cellforge_pcc_de", "r2_top", "pearson_delta_top", "direction_acc_top", "delta_scale_ratio")


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_write(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def _save_arrays(path: Path, arrays: dict) -> None:
    temporary = path.with_suffix(".tmp.npz")
    np.savez_compressed(temporary, **arrays)
    temporary.replace(path)


class Budget:
    def __init__(self):
        self.start, self.fits = time.monotonic(), 0

    def check(self):
        if time.monotonic() - self.start >= MAX_SECONDS:
            raise TimeoutError("fixed B1 diagnostic deadline exceeded")

    def fit(self):
        self.check()
        if self.fits >= MAX_FITS:
            raise RuntimeError("fixed B1 diagnostic fit cap exceeded")
        self.fits += 1


@contextmanager
def _wall_alarm(seconds):
    def stop(signum, frame):
        raise TimeoutError("fixed B1 diagnostic deadline exceeded")

    previous = signal.getsignal(signal.SIGALRM)
    if any(signal.getitimer(signal.ITIMER_REAL)):
        raise RuntimeError("another wall timer is active")
    signal.signal(signal.SIGALRM, stop)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def _folds(ctx, seed):
    targets = {p: ctx.target_genes(p) for p in ctx.train_perts}
    folds = cv_folds_of(ctx.train_perts, OUTER_FOLDS, seed, targets)
    if len(folds) != OUTER_FOLDS or sorted(p for predict, _ in folds for p in predict) != sorted(ctx.train_perts):
        raise ValueError("fixed gene folds must partition every training condition")
    for predict, hide in folds:
        if not set(predict).issubset(hide) or len(ctx.without_train(hide).train_perts) < 3:
            raise ValueError("invalid or too-small gene-fold training view")
    return folds


def usable_external_targets(ctx) -> set[str]:
    """Coverage only: no training/validation response or normalized kernel criterion."""
    raw = ctx.knowledge(KNOWLEDGE)
    if raw is None:
        return set()
    genes = [str(g) for g in raw["genes"]]
    if len(set(genes)) != len(genes):
        raise ValueError("duplicate external gene metadata")
    measured = raw.get("measured", [True] * len(genes))
    if len(measured) != len(genes):
        raise ValueError("external measured metadata shape mismatch")
    positions = [i for i, g in enumerate(genes) if g in ctx.gene_index and bool(measured[i])]
    usable = set()
    for target, row in (raw.get("perts") or {}).items():
        if not isinstance(row, dict):
            continue
        try:
            cells = row.get("n_cells")
            if cells is not None and (not np.isfinite(float(cells)) or float(cells) <= 0):
                continue
            values = row.get("delta")
            if not isinstance(values, list) or len(values) != len(genes):
                continue
            numeric = np.asarray([np.nan if value is None else float(value) for value in values])
        except (TypeError, ValueError, OverflowError):
            continue
        if np.count_nonzero(np.isfinite(numeric[positions])) >= 3:
            usable.add(str(target))
    return usable


def fold_metadata(ctx, predict, hide, index, usable):
    view = ctx.without_train(hide)
    singles = {ctx.target_genes(p)[0] for p in view.train_perts if len(ctx.target_genes(p)) == 1}
    coverage = []
    for pert in predict:
        targets = sorted(set(ctx.target_genes(pert)))
        kind = "singleton" if len(targets) == 1 else "pair" if len(targets) == 2 else "other"
        external = sum(g in usable for g in targets)
        known = sum(g in singles for g in targets)
        group = "unknown" if not targets else "all" if external == len(targets) else "partial" if external else "none"
        coverage.append({"perturbation": pert, "targets": targets, "kind": kind,
                         "known_singletons": known, "unknown_contributions": len(targets) - known,
                         "usable_external_targets": external, "external_coverage": group})
    return {"fold_index": index, "predict": list(predict), "hide": list(hide),
            "train": list(view.train_perts), "coverage": coverage}


def _strata(perts, folds):
    membership = {p: [] for p in perts}
    for fold in folds:
        for row in fold["coverage"]:
            membership[row["perturbation"]] = [row["kind"], f"known_{row['known_singletons']}",
                f"{row['kind']}_known_{row['known_singletons']}", f"external_{row['external_coverage']}",
                f"{row['kind']}_external_{row['external_coverage']}"]
    names = sorted({name for groups in membership.values() for name in groups})
    return {name: [i for i, p in enumerate(perts) if name in membership[p]] for name in names}


def fit_member(view, predict, plugins, member, budget):
    if set(predict).intersection(view.train_perts):
        raise ValueError("predicted conditions remain in the training view")
    budget.check()
    previous = np.random.get_state()
    try:
        np.random.seed(member["seed"])
        with _plugins(plugins):
            # Match the frozen recipe's compute seed even if imports drew RNG.
            np.random.seed(member["seed"])
            train_x, columns = build_matrix(view, member["features"], member["feature_params"],
                                            view.train_perts, {}, cache_dir=None)
            budget.check()
            pred_x, pred_columns = build_matrix(view, member["features"], member["feature_params"],
                                               predict, {}, cache_dir=None)
            if columns != member["columns"] or pred_columns != columns:
                raise ValueError("fixed B1 member column order changed")
            mean, sd = train_x.mean(axis=0), train_x.std(axis=0)
            sd[sd == 0] = 1.0
            _, delta = view.train_delta()
            if delta.shape != (len(view.train_perts), view.n_genes) or not np.all(np.isfinite(delta)):
                raise ValueError("invalid training delta matrix")
            model = make_model("ridge", member["alpha"], member["seed"])
            budget.fit()
            model.fit((train_x - mean) / sd, delta.reshape(-1))
            budget.check()
            pred = model.predict((pred_x - mean) / sd).reshape(len(predict), view.n_genes)
            if not np.all(np.isfinite(pred)):
                raise ValueError("B1 member produced nonfinite predictions")
            return pred
    finally:
        np.random.set_state(previous)


def score_development(pred_delta, truth_delta, control, perts):
    pred, truth = pred_delta + control, truth_delta + control
    metrics = evaluate(pred, truth, control, perts)["metrics"]
    top = np.argsort(-np.abs(truth_delta), axis=1)[:, :20]
    metrics.update(cellforge(pred, truth, top))
    metrics["delta_scale_ratio"] = float(np.mean(np.abs(pred_delta)) / max(1e-12, float(np.mean(np.abs(truth_delta)))))
    result = {key: float(metrics[key]) for key in METRICS}
    if not all(np.isfinite(value) for value in result.values()):
        raise ValueError("nonfinite development metrics")
    return result


def _mean_sd(values):
    return {"mean": float(np.mean(values)), "sd": float(np.std(values, ddof=1)), "n_seeds": len(values)}


def aggregate(repeats, strata=None):
    rows = repeats if strata is None else [r["strata"][strata] for r in repeats if strata in r["strata"]]
    if len(rows) < 2:
        return {"n_seeds": len(rows), "mean_sd_over_seeds": {}, "paired_differences_over_seeds": {}}
    return {"n_seeds": len(rows),
        "mean_sd_over_seeds": {r: {m: _mean_sd([x["metrics"][r][m] for x in rows]) for m in METRICS} for r in RECIPES},
        "paired_differences_over_seeds": {r: {m: _mean_sd([x["metrics"][r][m] - x["metrics"]["additive"][m]
                                            for x in rows]) for m in METRICS} for r in RECIPES if r != "additive"}}


def fixed_config(package, manifest_hash, manifest, ctx, folds):
    import sklearn
    paths = ("tools/b1_development_diagnostic.py", "docs/B1_DIAGNOSTIC_PLAN.md", "genemila/features/api.py",
             "genemila/features/builtin.py", "genemila/features/registry.py", "genemila/frozen.py",
             "genemila/pipeline.py", "genemila/benchmark/evaluator.py", "genemila/benchmark/comparable.py",
             "docs/results/b1_development_diagnostic_20261013/run_with_deadline.py")
    return {"schema_version": 1, "status": "fixed_before_fitting", "package": str(package),
        "manifest_sha256": manifest_hash, "package_files_sha256": manifest["files_sha256"],
        "members": manifest["members"], "ensemble_weights": [1 / 3] * 3,
        "outer_seeds": list(SEEDS), "outer_folds": OUTER_FOLDS, "folds": folds,
        "batch_rule": "fresh member modules/context; training batch then complete predicted fold batch",
        "alpha_selection": "none; original fixed member alphas", "recipes": list(RECIPES),
        "metrics": list(METRICS), "top_genes": "20 largest absolute true development deltas; no cell-derived DE reference",
        "external_coverage": {"knowledge": KNOWLEDGE, "min_finite_measured_aligned_genes": 3,
                              "positive_n_cells_when_present": True, "normalized_kernel_requirement": False},
        "strata": "overlapping metadata-fixed target-count, known-singleton and external-coverage groups",
        "n_train": len(ctx.train_perts), "n_genes": ctx.n_genes,
        "train_order": list(ctx.train_perts), "genes": list(ctx.genes),
        "source_sha256": {name: _hash(REPO / name) for name in paths},
        "versions": {"python": platform.python_version(), "numpy": np.__version__, "scikit_learn": sklearn.__version__},
        "max_ridge_fits": MAX_FITS, "max_wall_seconds": MAX_SECONDS, "api_cost_usd": 0,
        "interpretation": "baseline diagnosis only; same-cohort fold sensitivity; historically selected B1 recipes; no promotion"}


def diagnose(ctx, package, manifest, folds_by_seed, summary, artifacts, budget, event):
    perts, positions = list(ctx.train_perts), {p: i for i, p in enumerate(ctx.train_perts)}
    for seed in SEEDS:
        predictions = {r: np.full((len(perts), ctx.n_genes), np.nan) for r in RECIPES}
        artifacts.update({f"seed_{seed}_{r}": array for r, array in predictions.items()})
        repeat = {"seed": seed, "status": "running", "folds": []}
        summary["repeats"].append(repeat)
        for meta in folds_by_seed[str(seed)]:
            budget.check()
            predict, hide = meta["predict"], meta["hide"]
            rows = [positions[p] for p in predict]
            event("fold_started", seed=seed, fold=meta["fold_index"])
            for index, member in enumerate(manifest["members"]):
                view = ctx.without_train(hide)  # fresh caches for every member/fold
                predictions[f"member_{index}"][rows] = fit_member(
                    view, predict, package / "members" / str(index) / "plugins", member, budget)
                event("member_completed", seed=seed, fold=meta["fold_index"], member=index)
            predictions["ensemble"][rows] = np.mean([predictions[f"member_{i}"][rows] for i in range(3)], axis=0)
            view = ctx.without_train(hide)
            predictions["additive"][rows] = AdditiveResponse().compute(view, predict, {})[:, :, 0]
            repeat["folds"].append(meta)
            event("fold_completed", seed=seed, fold=meta["fold_index"])
        _, truth = ctx.train_delta()  # full public training responses enter only frozen-prediction scoring
        repeat["metrics"] = {r: score_development(predictions[r], truth, ctx.control_mean, perts) for r in RECIPES}
        repeat["strata"] = {name: {"n_conditions": len(rows), "perturbations": [perts[i] for i in rows],
            "metrics": {r: score_development(predictions[r][rows], truth[rows], ctx.control_mean,
                                             [perts[i] for i in rows]) for r in RECIPES}}
            for name, rows in _strata(perts, folds_by_seed[str(seed)]).items() if rows}
        repeat["status"] = "complete"
        event("seed_completed", seed=seed)
    summary.update(aggregate(summary["repeats"]))
    groups = sorted({name for row in summary["repeats"] for name in row["strata"]})
    summary["strata_over_seeds"] = {name: aggregate(summary["repeats"], name) for name in groups}
    summary["status"] = "complete"
    if budget.fits != MAX_FITS:
        raise RuntimeError("completed run must contain exactly 45 B1 ridge fits")
    event("diagnostic_completed")


def run(package: Path, manifest_sha256: str, out: Path):
    package, out = package.resolve(), out.resolve()
    if out == package or package in out.parents or out in package.parents:
        raise ValueError("output must be separate from the input package")
    out.mkdir(parents=True, exist_ok=False)
    budget, artifacts = Budget(), {}
    summary = {"schema_version": 1, "status": "running", "run_directory": str(out), "repeats": [],
               "uncertainty": "sample SD across same-cohort fold seeds; partition sensitivity, not independent replication",
               "decision": "diagnostic only; no tuning or model promotion; delivered B1 unchanged"}

    def event(kind, **details):
        record = {"event": kind, "elapsed_s": time.monotonic() - budget.start, "fits": budget.fits, **details}
        with (out / "progress.jsonl").open("a") as stream:
            stream.write(json.dumps(record, allow_nan=False) + "\n")
        print(json.dumps(record, allow_nan=False), flush=True)
        summary["elapsed_s"], summary["fit_count"] = record["elapsed_s"], budget.fits
        _json_write(out / "summary.json", summary)
        if kind == "fold_completed":
            _save_arrays(out / "predictions.npz", artifacts)

    try:
        with _wall_alarm(MAX_SECONDS):
            if manifest_sha256 != MANIFEST_SHA256:
                raise ValueError("the protocol requires the fixed B1 manifest hash")
            manifest = load_export(package, manifest_sha256)
            identities = [(m["experiment_id"], m["alpha"], m["seed"], m["model_type"]) for m in manifest["members"]]
            if identities != [("EXP_0681", 20000.0, 1, "ridge"), ("EXP_0729", 0.00198, 2, "ridge"), ("EXP_0519", 300.0, 3, "ridge")]:
                raise ValueError("fixed B1 member identities changed")
            ctx = FeatureContext(package / "context", cache_dir=None)
            usable = usable_external_targets(ctx)
            folds = {str(seed): [fold_metadata(ctx, predict, hide, i, usable)
                for i, (predict, hide) in enumerate(_folds(ctx, seed))] for seed in SEEDS}
            _json_write(out / "config.json", fixed_config(package, manifest_sha256, manifest, ctx, folds))
            summary.update({"config_sha256": _hash(out / "config.json"), "n_train": len(ctx.train_perts),
                            "n_genes": ctx.n_genes, "scored_training_perturbations": list(ctx.train_perts)})
            artifacts["perturbations"] = np.asarray(ctx.train_perts, dtype=str)
            event("config_written")
            diagnose(ctx, package, manifest, folds, summary, artifacts, budget, event)
    except BaseException as exc:
        summary["status"] = "timed_out" if isinstance(exc, TimeoutError) else "interrupted" if isinstance(exc, KeyboardInterrupt) else "failed"
        summary["error"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        summary["elapsed_s"], summary["fit_count"] = time.monotonic() - budget.start, budget.fits
        if artifacts:
            _save_arrays(out / "predictions.npz", artifacts)
        _json_write(out / "summary.json", summary)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True, help="new exclusive directory under ignored runs/")
    args = parser.parse_args(argv)
    summary = run(args.package, args.manifest_sha256, args.out)
    print(json.dumps({"status": summary["status"], "run_directory": summary["run_directory"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
