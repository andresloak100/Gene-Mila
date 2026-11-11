"""Fixed, public-training-only singleton-transfer development comparison.

Read docs/SINGLETON_TRANSFER_PLAN.md before a real run. This standalone CPU
diagnostic never opens private labels, splits, an oracle, or an API provider.
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
from genemila.benchmark.evaluator import _pearson, evaluate  # noqa: E402
from genemila.features.api import FeatureContext  # noqa: E402
from genemila.features.builtin import AdditiveResponse, ControlMean, IsTarget, MeanResponse  # noqa: E402
from genemila.features.plugins import singleton_transfer as transfer  # noqa: E402
from genemila.frozen import _plugins, load_export  # noqa: E402
from genemila.pipeline import build_matrix, cv_folds_of, make_model  # noqa: E402

ALPHAS = (0.01, 1.0, 100.0, 10000.0, 1000000.0)
SEEDS = (0, 1, 2)
OUTER_FOLDS = 5
INNER_FOLDS = 3
MAX_SECONDS = 7200
MANIFEST_SHA256 = "225adc3079251f3cd17f16999b3bc92ab18ae20e9fcde9ee0617b8f350869b45"
ARMS = ("control", "candidate")
RECIPES_A = ARMS + ("analytic_additive", "direct_external_additive", "singleton_transfer_additive")
METRICS = (
    "pearson_delta", "mse", "pearson_expr", "cellforge_r2", "mse_top",
    "cellforge_pcc_de", "r2_top", "pearson_delta_top", "direction_acc_top",
    "delta_scale_ratio",
)


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_write(path: Path, value: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def _order_hash(values: list[str]) -> str:
    return hashlib.sha256(json.dumps(values, ensure_ascii=False).encode()).hexdigest()


class Budget:
    """One wall deadline and fixed fit caps; neither is chosen from scores."""

    def __init__(self, seconds: float = MAX_SECONDS):
        self.start = time.monotonic()
        self.deadline = self.start + seconds
        self.fits = {"A": 0, "B": 0}

    def check(self) -> None:
        if time.monotonic() >= self.deadline:
            raise TimeoutError("fixed development diagnostic wall deadline exceeded")

    def fit(self, stage: str) -> None:
        self.check()
        self.fits[stage] += 1
        if self.fits[stage] > {"A": 480, "B": 90}[stage]:
            raise RuntimeError("predeclared ridge fit cap exceeded")


@contextmanager
def _wall_alarm(seconds: float):
    """Interrupt a long native operation at the fixed deadline where supported."""
    def stop(signum, frame):
        raise TimeoutError("fixed development diagnostic wall deadline exceeded")

    previous = signal.getsignal(signal.SIGALRM)
    old_timer = signal.getitimer(signal.ITIMER_REAL)
    if old_timer[0] or old_timer[1]:
        raise RuntimeError("another process wall timer is already active")
    signal.signal(signal.SIGALRM, stop)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def fixed_config(package: Path, manifest_hash: str, manifest: dict, ctx: FeatureContext) -> dict:
    import sklearn
    source_paths = (
        "tools/singleton_transfer_diagnostic.py", "docs/SINGLETON_TRANSFER_PLAN.md",
        "genemila/features/plugins/singleton_transfer.py", "genemila/features/api.py",
        "genemila/features/builtin.py", "genemila/features/registry.py", "genemila/frozen.py",
        "genemila/pipeline.py", "genemila/benchmark/evaluator.py", "genemila/benchmark/comparable.py",
        "docs/results/singleton_transfer_development_20261013/run_with_deadline.py",
    )
    # The verified receipt pins every public input and every member plugin, as
    # well as the saved numeric models (which this diagnostic never uses).
    return {
        "schema_version": 1, "status": "fixed_before_fitting", "package": str(package),
        "manifest_sha256": manifest_hash, "package_files_sha256": manifest["files_sha256"],
        "label_scope": "public training only; nested development folds",
        "stage_a_control": ["control_mean", "mean_response", "is_target", "additive_response", "ordinary_external_transfer"],
        "stage_a_candidate": ["control_mean", "mean_response", "is_target", "singleton_transfer_additive", "ordinary_external_transfer"],
        "diagnostic_rules": list(RECIPES_A[2:]), "external_kernel_lambda": 1.0,
        "external_knowledge": transfer.KNOWLEDGE, "alphas": list(ALPHAS),
        "outer_seeds": list(SEEDS), "outer_folds": OUTER_FOLDS, "inner_folds": INNER_FOLDS,
        "inner_seed_rule": "1000 + 100 * outer_seed + outer_fold_index",
        "alpha_selection": "inner OOF mean Pearson delta; smaller alpha wins exact ties",
        "stage_b_members": manifest["members"], "stage_b_weights": [1 / 3] * 3,
        "stage_b_change": "append singleton_transfer_correction; original fixed per-member alpha/seed",
        "stage_b_batch_rule": "fresh member modules and restricted context; train batch then full predicted fold batch",
        "gate": {"paired_pearson_each_positive": True, "mean_gain_strictly_exceeds": "max(0.002, sample SD of gains)",
                 "max_ratio_of_across_seed_mean_mse": 1.01, "max_ratio_of_across_seed_mean_mse_top": 1.01},
        "metrics": list(METRICS), "top_genes": "20 highest absolute true development delta; no cell-derived DE reference",
        "n_train": len(ctx.train_perts), "n_genes": ctx.n_genes,
        "train_order_sha256": _order_hash(ctx.train_perts), "gene_order_sha256": _order_hash(ctx.genes),
        "source_sha256": {name: _hash(REPO / name) for name in source_paths},
        "versions": {"python": platform.python_version(), "numpy": np.__version__, "scikit_learn": sklearn.__version__},
        "max_ridge_fits": {"A": 480, "B": 90}, "max_wall_seconds": MAX_SECONDS, "api_cost_usd": 0,
        "interpretation": "development screen only; seeds reuse cohort; B1 recipes historically selected on this cohort; no deployment",
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
    if sorted(p for predict, _ in folds for p in predict) != sorted(ctx.train_perts):
        raise ValueError("development folds do not partition the training perturbations")
    for predict, hide in folds:
        if not predict or not set(predict).issubset(hide):
            raise ValueError("invalid gene-grouped fold")
        _check_context(ctx.without_train(hide))
    return folds


def _column(cls, ctx: FeatureContext, perts: list[str]) -> np.ndarray:
    values = np.asarray(cls().compute(ctx, perts, {}), dtype=np.float64)
    if values.shape != (len(perts), ctx.n_genes, 1) or not np.isfinite(values).all():
        raise ValueError("invalid one-column feature output")
    return values.reshape(len(perts) * ctx.n_genes, 1)


def _matrices(ctx: FeatureContext, perts: list[str]) -> dict:
    common = [_column(cls, ctx, perts) for cls in (ControlMean, MeanResponse, IsTarget)]
    ordinary = _column(transfer.OrdinaryExternalTransfer, ctx, perts)
    return {"control": np.hstack([*common, _column(AdditiveResponse, ctx, perts), ordinary]),
            "candidate": np.hstack([*common, _column(transfer.SingletonTransferAdditive, ctx, perts), ordinary])}


def _ridge_predictions(train_x, pred_x, truth, alphas, seed, budget, stage):
    if not np.isfinite(train_x).all() or not np.isfinite(pred_x).all():
        raise ValueError("nonfinite feature matrix")
    mu, sd = train_x.mean(axis=0), train_x.std(axis=0)
    sd[sd == 0] = 1.0
    train_x, pred_x = (train_x - mu) / sd, (pred_x - mu) / sd
    out = {}
    for alpha in alphas:
        budget.fit(stage)
        model = make_model("ridge", alpha, seed)
        model.fit(train_x, truth.reshape(-1))
        values = model.predict(pred_x).reshape(-1, truth.shape[1])
        budget.check()
        if not np.isfinite(values).all():
            raise ValueError("nonfinite ridge predictions")
        out[alpha] = values
    return out


def _fit_predictions(ctx: FeatureContext, perts: list[str], alphas_by_arm: dict, seed: int,
                     budget: Budget | None = None):
    """Regenerate both arms' matrices using only the provided restricted view."""
    budget = budget or Budget()
    budget.check()
    _check_context(ctx)
    if set(perts).intersection(ctx.train_perts):
        raise ValueError("scored fold perturbations remain in the fitting view")
    train_x = _matrices(ctx, ctx.train_perts)
    budget.check()
    pred_x = _matrices(ctx, perts)
    budget.check()
    _, truth = ctx.train_delta()
    return {arm: _ridge_predictions(train_x[arm], pred_x[arm], truth, alphas_by_arm[arm], seed, budget, "A")
            for arm in ARMS}


def _pearson_delta(pred, truth) -> float:
    return float(np.mean([_pearson(p, d) for p, d in zip(pred, truth)]))


def fit_outer(ctx: FeatureContext, predict: list[str], hide: list[str], seed: int, fold_index: int,
              budget: Budget | None = None):
    """Outer labels cannot enter nested alpha choice, features, or the final fit."""
    budget = budget or Budget()
    if not set(predict).issubset(hide):
        raise ValueError("outer predictions must belong to the hidden set")
    view = ctx.without_train(hide)
    _check_context(view)
    inner_seed = 1000 + 100 * seed + fold_index
    positions = {p: i for i, p in enumerate(view.train_perts)}
    oof = {arm: {a: np.zeros((len(view.train_perts), view.n_genes)) for a in ALPHAS} for arm in ARMS}
    inner_memberships = []
    for fold, inner_hide in _folds(view, INNER_FOLDS, inner_seed):
        inner_view = view.without_train(inner_hide)
        predictions = _fit_predictions(inner_view, fold, {arm: ALPHAS for arm in ARMS}, inner_seed, budget)
        rows = [positions[p] for p in fold]
        for arm in ARMS:
            for alpha in ALPHAS:
                oof[arm][alpha][rows] = predictions[arm][alpha]
        inner_memberships.append({"predict": fold, "hide": inner_hide, "train": inner_view.train_perts})
    _, truth = view.train_delta()
    scores = {arm: {a: _pearson_delta(oof[arm][a], truth) for a in ALPHAS} for arm in ARMS}
    if not all(np.isfinite(s) for values in scores.values() for s in values.values()):
        raise ValueError("nonfinite inner selection score")
    selected = {arm: max(ALPHAS, key=lambda a: (scores[arm][a], -a)) for arm in ARMS}
    final = _fit_predictions(view, predict, {arm: (selected[arm],) for arm in ARMS}, seed, budget)
    out = {arm: final[arm][selected[arm]] for arm in ARMS}
    for name, cls in (("analytic_additive", AdditiveResponse),
                      ("direct_external_additive", transfer.DirectExternalAdditive),
                      ("singleton_transfer_additive", transfer.SingletonTransferAdditive)):
        budget.check()
        out[name] = _column(cls, view, predict).reshape(len(predict), view.n_genes)
    return out, {"fold_index": fold_index, "inner_seed": inner_seed, "predict": predict,
                 "hide": hide, "train": view.train_perts, "inner_folds": inner_memberships,
                 "selected_alpha": selected, "inner_selection_scores": {
                     arm: {str(a): value for a, value in scores[arm].items()} for arm in ARMS},
                 "coverage": transfer.singleton_coverage(view, predict)}


def fit_b1_outer(ctx: FeatureContext, predict: list[str], hide: list[str], package: Path,
                 members: list[dict], budget: Budget):
    if not set(predict).issubset(hide):
        raise ValueError("outer predictions must belong to the hidden set")
    individual = {arm: [] for arm in ARMS}
    metadata = []
    for index, member in enumerate(members):
        budget.check()
        with _plugins(package / "members" / str(index) / "plugins"):
            # Never call frozen._matrix: it deliberately restores all training
            # labels for frozen inference, which would invalidate this refit.
            view = ctx.without_train(hide)
            _check_context(view)
            np.random.seed(int(member["seed"]))
            train_x, columns = build_matrix(view, member["features"], member["feature_params"],
                                            view.train_perts, {}, cache_dir=None)
            budget.check()
            pred_x, eval_columns = build_matrix(view, member["features"], member["feature_params"],
                                                predict, {}, cache_dir=None)
            if columns != member["columns"] or eval_columns != columns:
                raise ValueError("B1 recipe column order changed")
            correction_train = _column(transfer.SingletonTransferCorrection, view, view.train_perts)
            correction_pred = _column(transfer.SingletonTransferCorrection, view, predict)
            _, truth = view.train_delta()
            alpha = float(member["alpha"])
            for arm in ARMS:
                tx = train_x if arm == "control" else np.hstack([train_x, correction_train])
                px = pred_x if arm == "control" else np.hstack([pred_x, correction_pred])
                values = _ridge_predictions(tx, px, truth, (alpha,), int(member["seed"]), budget, "B")
                individual[arm].append(values[alpha])
            metadata.append({"member_index": index, "experiment_id": member["experiment_id"],
                             "alpha": alpha, "seed": member["seed"], "columns": columns})
    out = {arm: np.mean(individual[arm], axis=0) for arm in ARMS}
    for arm in ARMS:
        out.update({f"{arm}_member_{i}": values for i, values in enumerate(individual[arm])})
    return out, {"predict": predict, "hide": hide, "train": ctx.without_train(hide).train_perts,
                 "members": metadata, "coverage": transfer.singleton_coverage(ctx.without_train(hide), predict)}


def score_development(pred_delta, truth_delta, control, perts) -> dict:
    pred, truth = pred_delta + control, truth_delta + control
    metrics = evaluate(pred, truth, control, perts)["metrics"]
    top = np.argsort(-np.abs(truth_delta), axis=1)[:, :20]
    metrics.update(cellforge(pred, truth, top))
    metrics["delta_scale_ratio"] = float(np.mean(np.abs(pred_delta)) / max(1e-12, float(np.mean(np.abs(truth_delta)))))
    out = {key: float(metrics[key]) for key in METRICS}
    if not all(np.isfinite(v) for v in out.values()):
        raise ValueError("nonfinite development metrics")
    return out


def _mean_sd(values) -> dict:
    return {"mean": float(np.mean(values)), "sd": float(np.std(values, ddof=1)), "n_seeds": len(values)}


def gate(repeats: list[dict]) -> dict:
    if len(repeats) != 3:
        raise ValueError("the fixed gate requires all three completed repeats")
    gains = [r["metrics"]["candidate"]["pearson_delta"] - r["metrics"]["control"]["pearson_delta"] for r in repeats]
    summary = _mean_sd(gains)
    threshold = max(0.002, summary["sd"])
    errors = {}
    for metric in ("mse", "mse_top"):
        baseline = float(np.mean([r["metrics"]["control"][metric] for r in repeats]))
        candidate = float(np.mean([r["metrics"]["candidate"][metric] for r in repeats]))
        errors[metric] = {"control_mean": baseline, "candidate_mean": candidate,
                          "ratio": candidate / baseline if baseline > 0 else (1.0 if candidate == 0 else None),
                          "passed": candidate <= 1.01 * baseline}
    checks = {"all_gains_positive": all(g > 0 for g in gains),
              "mean_gain_above_threshold": summary["mean"] > threshold,
              **{f"{metric}_within_one_percent": value["passed"] for metric, value in errors.items()}}
    return {"passed": all(checks.values()), "checks": checks, "paired_pearson_gains": gains,
            "paired_gain_mean_sd": summary, "strict_threshold": threshold, "error_guardrails": errors,
            "interpretation": "predeclared development screening heuristic, not a significance test"}


def _aggregate(stage: dict, recipes: tuple[str, ...]) -> None:
    repeats = stage["repeats"]
    stage["mean_sd_over_seeds"] = {r: {m: _mean_sd([x["metrics"][r][m] for x in repeats]) for m in METRICS} for r in recipes}
    stage["paired_differences_over_seeds"] = {
        r: {m: _mean_sd([x["metrics"][r][m] - x["metrics"]["control"][m] for x in repeats]) for m in METRICS}
        for r in recipes if r != "control"}
    if "control_member_0" in recipes:
        stage["paired_member_ablation_differences_over_seeds"] = {
            str(i): {m: _mean_sd([x["metrics"][f"candidate_member_{i}"][m]
                                 - x["metrics"][f"control_member_{i}"][m] for x in repeats])
                     for m in METRICS} for i in range(3)}
    stage["gate"] = gate(repeats)
    stage["status"] = "complete"


def _strata(ctx: FeatureContext, perts: list[str], folds: list[dict]) -> dict:
    groups = {}
    for fold in folds:
        view = ctx.without_train(fold["hide"])
        singles = {view.target_genes(p)[0] for p in view.train_perts if len(view.target_genes(p)) == 1}
        for pert in fold["predict"]:
            targets = sorted(set(ctx.target_genes(pert)))
            kind = "singleton" if len(targets) == 1 else "pair" if len(targets) == 2 else "other"
            known = sum(t in singles for t in targets)
            for group in (kind, f"{kind}_known_{known}"):
                groups.setdefault(group, []).append(pert)
    return {name: [i for i, p in enumerate(perts) if p in set(names)] for name, names in sorted(groups.items())}


def diagnose(ctx: FeatureContext, package: Path, manifest: dict, summary: dict, artifacts: dict,
             budget: Budget, event) -> None:
    _check_context(ctx)
    perts = list(ctx.train_perts)
    positions = {p: i for i, p in enumerate(perts)}
    # The split construction sees metadata only. Retain exact memberships for
    # both stages so conditional continuation cannot change the comparison.
    folds_by_seed = {seed: _folds(ctx, OUTER_FOLDS, seed) for seed in SEEDS}
    for label in ("A", "B"):
        if label == "B" and not summary["stages"]["A"]["gate"]["passed"]:
            summary["stages"]["B"] = {"status": "skipped", "reason": "Stage A fixed gate failed"}
            event("stage_skipped", stage="B")
            break
        recipes = RECIPES_A if label == "A" else ARMS + tuple(f"{arm}_member_{i}" for arm in ARMS for i in range(3))
        stage = {"status": "running", "repeats": []}
        summary["stages"][label] = stage
        for seed in SEEDS:
            predictions = {r: np.full((len(perts), ctx.n_genes), np.nan) for r in recipes}
            for recipe, values in predictions.items():
                artifacts[f"stage_{label}_seed_{seed}_{recipe}"] = values
            repeat = {"seed": seed, "status": "running", "folds": []}
            stage["repeats"].append(repeat)
            for index, (fold, hide) in enumerate(folds_by_seed[seed]):
                budget.check()
                event("fold_started", stage=label, seed=seed, fold=index)
                if label == "A":
                    values, meta = fit_outer(ctx, fold, hide, seed, index, budget)
                else:
                    values, meta = fit_b1_outer(ctx, fold, hide, package, manifest["members"], budget)
                    meta["fold_index"] = index
                rows = [positions[p] for p in fold]
                for recipe in recipes:
                    predictions[recipe][rows] = values[recipe]
                repeat["folds"].append(meta)
                event("fold_completed", stage=label, seed=seed, fold=index, fits=dict(budget.fits))
            # Only the scoring block can access complete public-training truth.
            _, truth = ctx.train_delta()
            repeat["metrics"] = {r: score_development(predictions[r], truth, ctx.control_mean, perts) for r in recipes}
            repeat["strata"] = {
                name: {"n_conditions": len(rows), "perturbations": [perts[i] for i in rows],
                       "metrics": {r: score_development(predictions[r][rows], truth[rows], ctx.control_mean,
                                                        [perts[i] for i in rows]) for r in recipes}}
                for name, rows in _strata(ctx, perts, repeat["folds"]).items() if rows}
            repeat["status"] = "complete"
            event("seed_completed", stage=label, seed=seed)
        _aggregate(stage, recipes)
        event("stage_completed", stage=label, passed=stage["gate"]["passed"])
    summary["status"] = "complete"
    summary["decision"] = ("candidate for independent validation; B1 remains unchanged"
                           if summary["stages"]["B"].get("gate", {}).get("passed")
                           else "no promotion; B1 remains unchanged")


def run(package: Path, manifest_sha256: str, out: Path) -> dict:
    package, out = package.resolve(), out.resolve()
    if out == package or package in out.parents or out in package.parents:
        raise ValueError("output must be separate from the input package")
    out.mkdir(parents=True, exist_ok=False)
    budget = Budget()
    summary = {"schema_version": 1, "status": "running", "run_directory": str(out),
               "label_scope": "public training development only", "stages": {},
               "uncertainty": "sample SD across same-cohort fold seeds; partition sensitivity, not independent replication"}
    artifacts = {}

    def event(kind, **details):
        record = {"event": kind, "elapsed_s": time.monotonic() - budget.start, **details}
        with (out / "progress.jsonl").open("a") as stream:
            stream.write(json.dumps(record, allow_nan=False) + "\n")
        print(json.dumps(record, allow_nan=False), flush=True)
        summary["elapsed_s"], summary["fit_counts"] = record["elapsed_s"], dict(budget.fits)
        _json_write(out / "summary.json", summary)

    try:
        with _wall_alarm(MAX_SECONDS):
            if manifest_sha256 != MANIFEST_SHA256:
                raise ValueError("the prospective protocol requires the fixed B1 manifest hash")
            manifest = load_export(package, manifest_sha256)
            if len(manifest["members"]) != 3 or any(m["model_type"] != "ridge" for m in manifest["members"]):
                raise ValueError("the fixed B1 protocol requires three ridge members")
            ctx = FeatureContext(package / "context", cache_dir=None)
            config = fixed_config(package, manifest_sha256, manifest, ctx)
            _json_write(out / "config.json", config)
            summary.update({"config_sha256": _hash(out / "config.json"), "n_train": len(ctx.train_perts),
                            "n_genes": ctx.n_genes, "scored_training_perturbations": list(ctx.train_perts)})
            artifacts["perturbations"] = np.asarray(ctx.train_perts, dtype=str)
            event("config_written")
            diagnose(ctx, package, manifest, summary, artifacts, budget, event)
    except BaseException as exc:
        summary["status"] = "timed_out" if isinstance(exc, TimeoutError) else "interrupted" if isinstance(exc, KeyboardInterrupt) else "failed"
        summary["error"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        summary["elapsed_s"], summary["fit_counts"] = time.monotonic() - budget.start, dict(budget.fits)
        if artifacts:
            np.savez_compressed(out / "predictions.npz", **artifacts)
        _json_write(out / "summary.json", summary)
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True, help="new exclusive directory, normally under ignored runs/")
    args = parser.parse_args(argv)
    summary = run(args.package, args.manifest_sha256, args.out)
    print(json.dumps({"run_directory": summary["run_directory"], "status": summary["status"],
                      "decision": summary["decision"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
