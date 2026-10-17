"""One fixed r2 ridge-penalty comparison on public gene-hidden folds.

Read docs/B1_R2_REGULARIZATION_PLAN.md before fitting. All original
features/batch rules remain fixed; only the cloned r2 alpha changes.
"""
from __future__ import annotations

import argparse
import copy
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from tools import b1_development_diagnostic as base  # noqa: E402

SEEDS, NEW_ALPHA, MAX_FITS, MAX_SECONDS = (9, 10, 11), 20000.0, 45, 7200
ARMS = ("candidate", "fixed_ensemble", "additive", "member_0", "member_1", "regularized_member_1")
GATE = {"mse_gain_each_positive": True, "mse_gain_mean_strictly_above_sample_sd": True,
        "max_candidate_mean_mse_ratio_to_additive": 1.01,
        "max_candidate_mean_mse_top_ratio_to_additive": 1.01,
        "max_candidate_mean_mse_top_ratio_to_fixed_ensemble": 1.01,
        "min_pearson_change_each": -0.01, "min_pearson_change_mean": -0.002}


def regularized_spec(original):
    variant = copy.deepcopy(original)
    variant["alpha"] = NEW_ALPHA
    return variant


def fit_outer(ctx, package, members, meta, budget, *, event=lambda *args, **kwargs: None,
              store=lambda arm, values: None):
    predictions = {}
    specs = (("member_0", 0, members[0]), ("member_1", 1, members[1]),
             ("regularized_member_1", 1, regularized_spec(members[1])))
    for arm, index, member in specs:
        view = ctx.without_train(meta["hide"])
        if view.train_perts != meta["train"]:
            raise ValueError("fixed fold training condition order changed")
        predictions[arm] = base.fit_member(view, meta["predict"],
            package / "members" / str(index) / "plugins", member, budget)
        store(arm, predictions[arm])
        event("member_completed", arm=arm)
    predictions["fixed_ensemble"] = (predictions["member_0"] + predictions["member_1"]) / 2
    predictions["candidate"] = (predictions["member_0"] + predictions["regularized_member_1"]) / 2
    predictions["additive"] = base.AdditiveResponse().compute(ctx.without_train(meta["hide"]), meta["predict"], {})[:, :, 0]
    for arm in ("fixed_ensemble", "candidate", "additive"):
        store(arm, predictions[arm])
    return predictions


def gate(repeats):
    if len(repeats) != 3:
        raise ValueError("the fixed regularization gate requires three completed repeats")
    gains = [r["metrics"]["fixed_ensemble"]["mse"] - r["metrics"]["candidate"]["mse"] for r in repeats]
    changes = [r["metrics"]["candidate"]["pearson_delta"] - r["metrics"]["fixed_ensemble"]["pearson_delta"] for r in repeats]
    primary, pearson = base._mean_sd(gains), base._mean_sd(changes)
    checks = {"mse_gain_each_positive": all(g > 0 for g in gains), "mse_gain_mean_above_sd": primary["mean"] > primary["sd"],
              "pearson_each_above_min": all(c >= -0.01 for c in changes), "pearson_mean_above_min": pearson["mean"] >= -0.002}
    ratios = {}
    for metric, reference in (("mse", "additive"), ("mse_top", "additive"), ("mse_top", "fixed_ensemble")):
        candidate = float(np.mean([r["metrics"]["candidate"][metric] for r in repeats]))
        comparator = float(np.mean([r["metrics"][reference][metric] for r in repeats]))
        name, passed = f"{metric}_to_{reference}", candidate <= 1.01 * comparator
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
    paths = ("tools/b1_r2_regularization.py", "docs/B1_R2_REGULARIZATION_PLAN.md", "tools/b1_development_diagnostic.py",
        "docs/B1_DIAGNOSTIC_PLAN.md", "genemila/features/api.py", "genemila/features/builtin.py", "genemila/features/registry.py",
        "genemila/frozen.py", "genemila/pipeline.py", "genemila/benchmark/evaluator.py", "genemila/benchmark/comparable.py",
        "docs/results/b1_r2_regularization_20261013/run_with_deadline.py")
    return {"schema_version": 1, "status": "fixed_before_fitting", "package": str(package), "manifest_sha256": manifest_sha256,
        "package_files_sha256": manifest["files_sha256"], "original_members": manifest["members"],
        "variant": regularized_spec(manifest["members"][1]), "variant_change": {"alpha": {"from": .00198, "to": NEW_ALPHA}},
        "outer_seeds": list(SEEDS), "outer_folds": 5, "folds": folds, "recipes": list(ARMS), "metrics": list(base.METRICS),
        "control": "equal mean of shared member0 and original member1", "candidate": "equal mean of shared member0 and regularized member1",
        "variant_plugin_snapshot": "members/1/plugins", "gate": dict(GATE),
        "batch_rule": "fresh restricted context/modules; original member seed; train batch then whole predicted fold batch",
        "source_limits": "original whole-batch fallback, internal kernel and external-input assumptions preserved; no feature repairs",
        "top_genes": "20 largest absolute true development deltas; no cell-derived DE reference",
        "n_train": len(ctx.train_perts), "n_genes": ctx.n_genes, "train_order": list(ctx.train_perts), "genes": list(ctx.genes),
        "source_sha256": {name: base._hash(REPO / name) for name in paths},
        "versions": {"python": platform.python_version(), "numpy": np.__version__, "scikit_learn": sklearn.__version__},
        "max_ridge_fits": MAX_FITS, "max_wall_seconds": MAX_SECONDS, "api_cost_usd": 0,
        "interpretation": "one fixed penalty test on historically selected cohort; no automatic model promotion"}


def run(package: Path, manifest_sha256: str, out: Path):
    package, out = package.resolve(), out.resolve()
    if out == package or package in out.parents or out in package.parents:
        raise ValueError("output must be separate from the input package")
    out.mkdir(parents=True, exist_ok=False)
    budget, artifacts = base.Budget(), {}
    summary = {"schema_version": 1, "status": "running", "run_directory": str(out), "repeats": [],
               "label_scope": "public training only; gene-hidden folds", "uncertainty": "same-cohort partition sensitivity; historical feature selection remains"}

    def event(kind, **details):
        record = {"event": kind, "elapsed_s": time.monotonic() - budget.start, "fit_count": budget.fits, **details}
        with (out / "progress.jsonl").open("a") as stream:
            stream.write(json.dumps(record, allow_nan=False) + "\n")
        print(json.dumps(record, allow_nan=False), flush=True)
        summary["elapsed_s"], summary["fit_count"] = record["elapsed_s"], budget.fits
        base._json_write(out / "summary.json", summary)
        if kind == "fold_completed":
            base._save_arrays(out / "predictions.npz", artifacts)

    try:
        with base._wall_alarm(MAX_SECONDS):
            if manifest_sha256 != base.MANIFEST_SHA256:
                raise ValueError("the protocol requires the fixed B1 manifest hash")
            manifest = base.load_export(package, manifest_sha256)
            identities = [(m["experiment_id"], m["alpha"], m["seed"], m["model_type"]) for m in manifest["members"]]
            if identities != [("EXP_0681", 20000., 1, "ridge"), ("EXP_0729", .00198, 2, "ridge"), ("EXP_0519", 300., 3, "ridge")]:
                raise ValueError("fixed B1 package member identities changed")
            ctx = base.FeatureContext(package / "context", cache_dir=None)
            usable = base.usable_external_targets(ctx)
            folds = {str(seed): [base.fold_metadata(ctx, predict, hide, i, usable)
                for i, (predict, hide) in enumerate(base._folds(ctx, seed))] for seed in SEEDS}
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
                    rows = [positions[p] for p in meta["predict"]]
                    event("fold_started", seed=seed, fold=meta["fold_index"])
                    fit_outer(ctx, package, manifest["members"], meta, budget,
                        event=lambda kind, **details: event(kind, seed=seed, fold=meta["fold_index"], **details),
                        store=lambda arm, values: predictions[arm].__setitem__(rows, values))
                    meta["status"] = "complete"
                    event("fold_completed", seed=seed, fold=meta["fold_index"])
                _, truth = ctx.train_delta()  # full public training truth only scores frozen predictions
                repeat["metrics"] = {arm: base.score_development(predictions[arm], truth, ctx.control_mean, perts) for arm in ARMS}
                repeat["strata"] = {name: {"n_conditions": len(rows), "perturbations": [perts[i] for i in rows],
                    "metrics": {arm: base.score_development(predictions[arm][rows], truth[rows], ctx.control_mean,
                        [perts[i] for i in rows]) for arm in ARMS}} for name, rows in base._strata(perts, folds[str(seed)]).items() if rows}
                repeat["status"] = "complete"
                event("seed_completed", seed=seed)
            if budget.fits != MAX_FITS:
                raise RuntimeError("completed regularization run must contain exactly 45 fits")
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
