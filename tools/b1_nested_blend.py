"""One nested MSE blend of additive and the fixed r1/r2 mean.

Read docs/B1_NESTED_BLEND_PLAN.md before fitting. Only public-training
responses enter restricted gene folds; no previous-run arrays are reused.
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from tools import b1_development_diagnostic as base  # noqa: E402

SEEDS, OUTER_FOLDS, INNER_FOLDS, MAX_FITS, MAX_SECONDS = (6, 7, 8), 5, 3, 120, 7200
ARMS = ("candidate", "fixed_ensemble", "additive", "member_0", "member_1")
GATE = {"mse_gain_each_positive": True, "mse_gain_mean_strictly_above_sample_sd": True,
        "max_candidate_mean_mse_ratio_to_additive": 1.01,
        "max_candidate_mean_mse_top_ratio_to_additive": 1.01,
        "max_candidate_mean_mse_top_ratio_to_fixed_ensemble": 1.01,
        "min_pearson_change_each": -0.01, "min_pearson_change_mean": -0.002}


class Budget(base.Budget):
    def check(self):
        if time.monotonic() - self.start >= MAX_SECONDS:
            raise TimeoutError("fixed nested blend deadline exceeded")

    def fit(self):
        self.check()
        if self.fits >= MAX_FITS:
            raise RuntimeError("fixed nested blend fit cap exceeded")
        self.fits += 1


def _folds(ctx, count, seed):
    targets = {p: ctx.target_genes(p) for p in ctx.train_perts}
    folds = base.cv_folds_of(ctx.train_perts, count, seed, targets)
    if len(folds) != count or sorted(p for predict, _ in folds for p in predict) != sorted(ctx.train_perts):
        raise ValueError("nested gene folds must partition every permitted condition")
    for predict, hide in folds:
        if not set(predict).issubset(hide) or len(ctx.without_train(hide).train_perts) < 3:
            raise ValueError("invalid or too-small nested gene training view")
    return folds


def memberships(ctx):
    usable = base.usable_external_targets(ctx)
    result = {}
    for seed in SEEDS:
        outer = []
        for index, (predict, hide) in enumerate(_folds(ctx, OUTER_FOLDS, seed)):
            meta = base.fold_metadata(ctx, predict, hide, index, usable)
            view = ctx.without_train(hide)
            inner_seed = 1000 + 100 * seed + index
            meta["inner_seed"], meta["inner_folds"] = inner_seed, []
            for j, (inner_predict, inner_hide) in enumerate(_folds(view, INNER_FOLDS, inner_seed)):
                inner = base.fold_metadata(view, inner_predict, inner_hide, j, usable)
                inner["hide_union"] = sorted(set(hide) | set(inner_hide))
                if inner["train"] != ctx.without_train(inner["hide_union"]).train_perts:
                    raise ValueError("outer/inner hide union does not match the restricted training order")
                meta["inner_folds"].append(inner)
            outer.append(meta)
        result[str(seed)] = outer
    return result


def learn_weight(additive, ensemble, truth):
    if additive.shape != ensemble.shape or truth.shape != additive.shape or not truth.size:
        raise ValueError("blend arrays must have equal nonempty shapes")
    if not all(np.all(np.isfinite(a)) for a in (additive, ensemble, truth)):
        raise ValueError("nonfinite or incomplete inner OOF arrays")
    difference = ensemble - additive
    numerator = float(np.sum(difference * (truth - additive)))
    denominator = float(np.sum(difference * difference))
    if not np.isfinite(numerator) or not np.isfinite(denominator):
        raise ValueError("nonfinite blend sufficient statistics")
    raw = numerator / denominator if denominator > 0 else 0.0
    if not np.isfinite(raw):
        raise ValueError("nonfinite unconstrained blend weight")
    weight = float(np.clip(raw, 0.0, 1.0))
    candidate = additive + weight * difference
    result = {"lambda": weight, "unclipped_lambda": raw, "numerator": numerator, "denominator": denominator,
            "zero_denominator": denominator == 0, "n_condition_gene_pairs": int(truth.size),
            "mse_additive": float(np.mean((additive - truth) ** 2)),
            "mse_fixed_ensemble": float(np.mean((ensemble - truth) ** 2)),
            "mse_blend": float(np.mean((candidate - truth) ** 2))}
    if not all(np.isfinite(result[name]) for name in ("mse_additive", "mse_fixed_ensemble", "mse_blend")):
        raise ValueError("nonfinite inner MSE objective")
    return result


def fit_outer(ctx, package, members, meta, budget, *, inner_path=None,
              event=lambda *args, **kwargs: None, store_outer=lambda arm, values: None):
    outer = ctx.without_train(meta["hide"])
    if outer.train_perts != meta["train"]:
        raise ValueError("outer training condition order changed")
    positions = {p: i for i, p in enumerate(outer.train_perts)}
    inner = {arm: np.full((len(positions), ctx.n_genes), np.nan)
             for arm in ("member_0", "member_1", "fixed_ensemble", "additive")}
    arrays = {"perturbations": np.asarray(outer.train_perts), **inner}
    try:
        for fold in meta["inner_folds"]:
            rows = [positions[p] for p in fold["predict"]]
            for index, member in enumerate(members[:2]):
                view = ctx.without_train(fold["hide_union"])
                if view.train_perts != fold["train"]:
                    raise ValueError("inner restricted training condition order changed")
                inner[f"member_{index}"][rows] = base.fit_member(view, fold["predict"],
                    package / "members" / str(index) / "plugins", member, budget)
                event("inner_member_completed", inner_fold=fold["fold_index"], member=index)
            inner["fixed_ensemble"][rows] = (inner["member_0"][rows] + inner["member_1"][rows]) / 2
            view = ctx.without_train(fold["hide_union"])
            inner["additive"][rows] = base.AdditiveResponse().compute(view, fold["predict"], {})[:, :, 0]
            if inner_path is not None:
                base._save_arrays(inner_path, arrays)
            event("inner_fold_completed", inner_fold=fold["fold_index"])
        _, truth = outer.train_delta()  # only permitted outer-training responses learn the scalar
        meta["weight_fit"] = learn_weight(inner["additive"], inner["fixed_ensemble"], truth)
        event("weight_learned", weight=meta["weight_fit"]["lambda"])
        predictions = {}
        for index, member in enumerate(members[:2]):
            view = ctx.without_train(meta["hide"])
            predictions[f"member_{index}"] = base.fit_member(view, meta["predict"],
                package / "members" / str(index) / "plugins", member, budget)
            store_outer(f"member_{index}", predictions[f"member_{index}"])
            event("outer_member_completed", member=index)
        predictions["fixed_ensemble"] = (predictions["member_0"] + predictions["member_1"]) / 2
        predictions["additive"] = base.AdditiveResponse().compute(ctx.without_train(meta["hide"]), meta["predict"], {})[:, :, 0]
        predictions["candidate"] = predictions["additive"] + meta["weight_fit"]["lambda"] * (predictions["fixed_ensemble"] - predictions["additive"])
        for arm in ("fixed_ensemble", "additive", "candidate"):
            store_outer(arm, predictions[arm])
        return predictions, arrays
    finally:
        if inner_path is not None:
            base._save_arrays(inner_path, arrays)
            meta["inner_oof_sha256"] = base._hash(inner_path)


def gate(repeats):
    if len(repeats) != 3:
        raise ValueError("the fixed blend gate requires all three completed repeats")
    gains = [r["metrics"]["fixed_ensemble"]["mse"] - r["metrics"]["candidate"]["mse"] for r in repeats]
    changes = [r["metrics"]["candidate"]["pearson_delta"] - r["metrics"]["fixed_ensemble"]["pearson_delta"] for r in repeats]
    primary, pearson = base._mean_sd(gains), base._mean_sd(changes)
    checks = {"mse_gain_each_positive": all(g > 0 for g in gains), "mse_gain_mean_above_sd": primary["mean"] > primary["sd"],
              "pearson_each_above_min": all(c >= -0.01 for c in changes), "pearson_mean_above_min": pearson["mean"] >= -0.002}
    ratios = {}
    for metric, reference in (("mse", "additive"), ("mse_top", "additive"), ("mse_top", "fixed_ensemble")):
        candidate = float(np.mean([r["metrics"]["candidate"][metric] for r in repeats]))
        comparator = float(np.mean([r["metrics"][reference][metric] for r in repeats]))
        name = f"{metric}_to_{reference}"
        passed = candidate <= 1.01 * comparator
        ratios[name] = {"candidate_mean": candidate, "reference_mean": comparator,
                       "ratio": candidate / comparator if comparator > 0 else 1.0 if candidate == 0 else None, "passed": passed}
        checks[f"{name}_within_one_percent"] = passed
    return {"passed": all(checks.values()), "checks": checks, "primary_mse_gains": gains, "primary_mse_gain_mean_sd": primary,
            "pearson_changes": changes, "pearson_change_mean_sd": pearson, "error_guardrails": ratios,
            "interpretation": "predeclared development screen; no significance or noninferiority claim"}


def aggregate(rows):
    def stats(values):
        return base._mean_sd(values) if len(values) > 1 else {"mean": float(values[0]), "sd": None, "n_seeds": 1}
    return {"n_seeds": len(rows),
        "mean_sd_over_seeds": {arm: {m: stats([r["metrics"][arm][m] for r in rows]) for m in base.METRICS} for arm in ARMS},
        "paired_differences_over_seeds": {reference: {arm: {m: stats([r["metrics"][arm][m] - r["metrics"][reference][m] for r in rows])
            for m in base.METRICS} for arm in ARMS if arm != reference} for reference in ("fixed_ensemble", "additive")}}


def fixed_config(package, manifest_sha256, manifest, ctx, folds):
    import sklearn
    paths = ("tools/b1_nested_blend.py", "docs/B1_NESTED_BLEND_PLAN.md", "tools/b1_development_diagnostic.py",
        "docs/B1_DIAGNOSTIC_PLAN.md", "genemila/features/api.py", "genemila/features/builtin.py",
        "genemila/features/registry.py", "genemila/frozen.py", "genemila/pipeline.py",
        "genemila/benchmark/evaluator.py", "genemila/benchmark/comparable.py",
        "docs/results/b1_nested_blend_20261013/run_with_deadline.py")
    return {"schema_version": 1, "status": "fixed_before_fitting", "package": str(package), "manifest_sha256": manifest_sha256,
        "package_files_sha256": manifest["files_sha256"], "participating_members": manifest["members"][:2],
        "retained_package_members": manifest["members"], "outer_seeds": list(SEEDS), "outer_folds": OUTER_FOLDS,
        "inner_folds": INNER_FOLDS, "inner_seed_rule": "1000 + 100*outer_seed + outer_fold_index", "folds": folds,
        "weight_rule": "clip(sum((E-A)*(Y-A))/sum((E-A)**2),0,1); exactly zero denominator ->0",
        "weight_training": "pooled all-gene MSE on inner OOF deltas; one scalar per outer fold; no intercept",
        "fixed_ensemble_weights": [.5, .5], "gate": dict(GATE), "recipes": list(ARMS), "metrics": list(base.METRICS),
        "batch_rule": "fresh restricted context/modules; original member seed; train batch then complete predicted fold batch",
        "top_genes": "20 largest absolute true development deltas; no cell-derived DE reference",
        "n_train": len(ctx.train_perts), "n_genes": ctx.n_genes, "train_order": list(ctx.train_perts), "genes": list(ctx.genes),
        "source_sha256": {name: base._hash(REPO / name) for name in paths},
        "versions": {"python": platform.python_version(), "numpy": np.__version__, "scikit_learn": sklearn.__version__},
        "max_member_fits": MAX_FITS, "max_wall_seconds": MAX_SECONDS, "api_cost_usd": 0,
        "interpretation": "nested development screen on historically selected cohort; no automatic promotion"}


def run(package: Path, manifest_sha256: str, out: Path):
    package, out = package.resolve(), out.resolve()
    if out == package or package in out.parents or out in package.parents:
        raise ValueError("output must be separate from the input package")
    out.mkdir(parents=True, exist_ok=False)
    (out / "inner_oof").mkdir()
    budget, artifacts = Budget(), {}
    summary = {"schema_version": 1, "status": "running", "run_directory": str(out), "repeats": [],
               "label_scope": "public training only; nested gene folds", "uncertainty": "same-cohort partition sensitivity; historical feature selection remains"}

    def event(kind, **details):
        record = {"event": kind, "elapsed_s": time.monotonic() - budget.start, "fit_count": budget.fits, **details}
        with (out / "progress.jsonl").open("a") as stream:
            stream.write(json.dumps(record, allow_nan=False) + "\n")
        print(json.dumps(record, allow_nan=False), flush=True)
        summary["elapsed_s"], summary["fit_count"] = record["elapsed_s"], budget.fits
        base._json_write(out / "summary.json", summary)
        if kind == "outer_fold_completed":
            base._save_arrays(out / "predictions.npz", artifacts)

    try:
        with base._wall_alarm(MAX_SECONDS):
            if manifest_sha256 != base.MANIFEST_SHA256:
                raise ValueError("the nested protocol requires the fixed B1 manifest hash")
            manifest = base.load_export(package, manifest_sha256)
            identities = [(m["experiment_id"], m["alpha"], m["seed"], m["model_type"]) for m in manifest["members"]]
            if identities != [("EXP_0681", 20000., 1, "ridge"), ("EXP_0729", .00198, 2, "ridge"), ("EXP_0519", 300., 3, "ridge")]:
                raise ValueError("fixed B1 package member identities changed")
            ctx = base.FeatureContext(package / "context", cache_dir=None)
            folds = memberships(ctx)  # all outer/inner metadata fixed before any fitting
            base._json_write(out / "config.json", fixed_config(package, manifest_sha256, manifest, ctx, folds))
            perts, positions = list(ctx.train_perts), {p: i for i, p in enumerate(ctx.train_perts)}
            summary.update({"config_sha256": base._hash(out / "config.json"), "n_train": len(perts), "n_genes": ctx.n_genes,
                            "scored_training_perturbations": perts})
            artifacts["perturbations"] = np.asarray(perts)
            event("config_written")
            for seed in SEEDS:
                predictions = {arm: np.full((len(perts), ctx.n_genes), np.nan) for arm in ARMS}
                artifacts.update({f"seed_{seed}_{arm}": array for arm, array in predictions.items()})
                repeat = {"seed": seed, "status": "running", "folds": []}
                summary["repeats"].append(repeat)
                for metadata in folds[str(seed)]:
                    budget.check()
                    meta = {**metadata, "status": "running"}
                    repeat["folds"].append(meta)
                    event("outer_fold_started", seed=seed, fold=meta["fold_index"])
                    path = out / "inner_oof" / f"seed_{seed}_fold_{meta['fold_index']}.npz"
                    meta["inner_oof_file"] = str(path.relative_to(out))
                    rows = [positions[p] for p in meta["predict"]]
                    values, _ = fit_outer(ctx, package, manifest["members"], meta, budget, inner_path=path,
                        event=lambda kind, **details: event(kind, seed=seed, fold=meta["fold_index"], **details),
                        store_outer=lambda arm, values: predictions[arm].__setitem__(rows, values))
                    for arm in ARMS:
                        predictions[arm][rows] = values[arm]
                    meta["status"], meta["inner_oof_file"] = "complete", str(path.relative_to(out))
                    event("outer_fold_completed", seed=seed, fold=meta["fold_index"])
                _, truth = ctx.train_delta()  # full training truth enters only frozen outer-prediction scoring
                repeat["metrics"] = {arm: base.score_development(predictions[arm], truth, ctx.control_mean, perts) for arm in ARMS}
                repeat["strata"] = {name: {"n_conditions": len(rows), "perturbations": [perts[i] for i in rows],
                    "metrics": {arm: base.score_development(predictions[arm][rows], truth[rows], ctx.control_mean,
                        [perts[i] for i in rows]) for arm in ARMS}} for name, rows in base._strata(perts, folds[str(seed)]).items() if rows}
                repeat["status"] = "complete"
                event("seed_completed", seed=seed)
            if budget.fits != MAX_FITS:
                raise RuntimeError("completed nested run must contain exactly 120 member fits")
            summary.update(aggregate(summary["repeats"]))
            groups = sorted({name for r in summary["repeats"] for name in r["strata"]})
            summary["strata_over_seeds"] = {name: aggregate([r["strata"][name] for r in summary["repeats"] if name in r["strata"]]) for name in groups}
            summary["gate"] = gate(summary["repeats"])
            summary["decision"] = "candidate for independent validation; B1 unchanged" if summary["gate"]["passed"] else "no promotion; B1 unchanged"
            summary["status"] = "complete"
            event("diagnostic_completed")
    except BaseException as exc:
        summary["status"] = "timed_out" if isinstance(exc, TimeoutError) else "interrupted" if isinstance(exc, KeyboardInterrupt) else "failed"
        summary["error"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        summary["elapsed_s"], summary["fit_count"] = time.monotonic() - budget.start, budget.fits
        if artifacts:
            base._save_arrays(out / "predictions.npz", artifacts)
        base._json_write(out / "summary.json", summary)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    summary = run(args.package, args.manifest_sha256, args.out)
    print(json.dumps({"status": summary["status"], "decision": summary["decision"], "run_directory": summary["run_directory"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
