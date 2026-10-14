"""One fixed composition comparison on new public-development fold seeds.

Read docs/B1_TWO_MEMBER_PLAN.md before fitting. Reuse the reviewed B1
fold-refit runner; the candidate averages members 0/1 from those same fits.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from tools import b1_development_diagnostic as base  # noqa: E402

SEEDS, WEIGHTS = (3, 4, 5), (0.5, 0.5, 0.0)
ARMS = ("candidate", "baseline", "additive")
GATE = {"all_paired_pearson_gains_positive": True,
        "mean_gain_strictly_above": "max(0.002, sample SD of paired gains)",
        "max_ratio_of_across_seed_mean_mse": 1.01,
        "max_ratio_of_across_seed_mean_mse_top": 1.01}


@contextmanager
def _fixed_comparison():
    seeds, config = base.SEEDS, base.fixed_config

    def fixed_config(*args, **kwargs):
        result = config(*args, **kwargs)
        paths = ("tools/b1_two_member_test.py", "docs/B1_TWO_MEMBER_PLAN.md",
                 "docs/results/b1_two_member_test_20261013/run_with_deadline.py")
        result["source_sha256"].update({name: base._hash(REPO / name) for name in paths})
        result["composition_comparison"] = {"purpose": "fixed two-member versus original three-member mean",
            "plan": "docs/B1_TWO_MEMBER_PLAN.md", "candidate_weights": list(WEIGHTS),
            "baseline_weights": [1 / 3] * 3, "fold_seeds": list(SEEDS), "gate": dict(GATE),
            "prior_diagnosis": "seeds 0/1/2 selected this hypothesis; no candidate scores calculated on them",
            "interpretation": "same-cohort development screen; no automatic promotion"}
        return result

    base.SEEDS, base.fixed_config = SEEDS, fixed_config
    try:
        yield
    finally:
        base.SEEDS, base.fixed_config = seeds, config


def gate(repeats):
    if len(repeats) != 3:
        raise ValueError("the fixed gate requires three completed fold-seed repeats")
    gains = [r["metrics"]["candidate"]["pearson_delta"] - r["metrics"]["baseline"]["pearson_delta"] for r in repeats]
    paired = base._mean_sd(gains)
    threshold = max(0.002, paired["sd"])
    checks = {"all_gains_positive": all(g > 0 for g in gains), "mean_gain_above_threshold": paired["mean"] > threshold}
    errors = {}
    for metric in ("mse", "mse_top"):
        reference = float(np.mean([r["metrics"]["baseline"][metric] for r in repeats]))
        candidate = float(np.mean([r["metrics"]["candidate"][metric] for r in repeats]))
        passed = candidate <= 1.01 * reference
        errors[metric] = {"baseline_mean": reference, "candidate_mean": candidate,
                         "ratio": candidate / reference if reference > 0 else 1.0 if candidate == 0 else None,
                         "passed": passed}
        checks[f"{metric}_within_one_percent"] = passed
    return {"passed": all(checks.values()), "checks": checks, "paired_pearson_gains": gains,
            "paired_gain_mean_sd": paired, "strict_threshold": threshold, "error_guardrails": errors,
            "interpretation": "predeclared development screening heuristic, not significance or independent validation"}


def _aggregate(rows):
    def stats(values):
        return base._mean_sd(values) if len(values) > 1 else {"mean": float(values[0]), "sd": None, "n_seeds": 1}
    return {"n_seeds": len(rows),
        "mean_sd_over_seeds": {arm: {m: stats([r["metrics"][arm][m] for r in rows]) for m in base.METRICS} for arm in ARMS},
        "paired_differences_over_seeds": {ref: {m: stats([r["metrics"]["candidate"][m] - r["metrics"][ref][m]
                                                    for r in rows]) for m in base.METRICS} for ref in ("baseline", "additive")}}


def run(package: Path, manifest_sha256: str, out: Path):
    package, out = package.resolve(), out.resolve()
    if out.exists():
        raise FileExistsError(out)
    started = time.monotonic()
    comparison = {"schema_version": 1, "status": "running", "run_directory": str(out), "repeats": [],
                  "candidate_weights": list(WEIGHTS), "fold_seeds": list(SEEDS),
                  "uncertainty": "same-cohort partition sensitivity; prior diagnosis informed this fixed hypothesis"}
    try:
        with _fixed_comparison():
            baseline = base.run(package, manifest_sha256, out)
        if baseline["status"] != "complete":
            raise ValueError("composition comparison requires complete baseline refits")
        comparison.update({"config_sha256": base._hash(out / "config.json"),
            "baseline_summary_sha256": base._hash(out / "summary.json"),
            "baseline_predictions_sha256": base._hash(out / "predictions.npz")})
        remaining = base.MAX_SECONDS - (time.monotonic() - started)
        if remaining <= 0:
            raise TimeoutError("fixed composition comparison deadline exceeded")
        with base._wall_alarm(remaining):
            with np.load(out / "predictions.npz", allow_pickle=False) as saved:
                perts = [str(p) for p in saved["perturbations"]]
                candidates = {f"seed_{seed}_candidate":
                    (saved[f"seed_{seed}_member_0"] + saved[f"seed_{seed}_member_1"]) / 2 for seed in SEEDS}
            if any(not np.all(np.isfinite(array)) for array in candidates.values()):
                raise ValueError("nonfinite shared member predictions")
            base._save_arrays(out / "candidate_predictions.npz", {"perturbations": np.asarray(perts), **candidates})
            comparison["candidate_predictions_sha256"] = base._hash(out / "candidate_predictions.npz")
            ctx = base.FeatureContext(package / "context", cache_dir=None)
            if perts != ctx.train_perts or perts != baseline["scored_training_perturbations"]:
                raise ValueError("shared prediction/public-training condition order mismatch")
            _, truth = ctx.train_delta()  # scoring only, after all fixed refits
            positions = {p: i for i, p in enumerate(perts)}
            if [r["seed"] for r in baseline["repeats"]] != list(SEEDS):
                raise ValueError("shared baseline fold seeds changed")
            for repeat in baseline["repeats"]:
                candidate = candidates[f"seed_{repeat['seed']}_candidate"]
                result = {"seed": repeat["seed"], "metrics": {"candidate": base.score_development(candidate, truth, ctx.control_mean, perts),
                    "baseline": repeat["metrics"]["ensemble"], "additive": repeat["metrics"]["additive"]}, "strata": {}}
                for name, stratum in repeat["strata"].items():
                    names = stratum["perturbations"]
                    rows = [positions[p] for p in names]
                    result["strata"][name] = {"n_conditions": len(rows), "perturbations": names,
                        "metrics": {"candidate": base.score_development(candidate[rows], truth[rows], ctx.control_mean, names),
                                    "baseline": stratum["metrics"]["ensemble"], "additive": stratum["metrics"]["additive"]}}
                comparison["repeats"].append(result)
                base._json_write(out / "comparison.json", comparison)
            comparison.update(_aggregate(comparison["repeats"]))
            groups = sorted({name for row in comparison["repeats"] for name in row["strata"]})
            comparison["strata_over_seeds"] = {name: _aggregate([r["strata"][name] for r in comparison["repeats"]
                if name in r["strata"]]) for name in groups}
            comparison["gate"] = gate(comparison["repeats"])
            comparison["decision"] = "candidate for independent validation; B1 unchanged" if comparison["gate"]["passed"] else "no promotion; B1 unchanged"
            comparison["status"] = "complete"
    except BaseException as exc:
        comparison["status"] = "timed_out" if isinstance(exc, TimeoutError) else "interrupted" if isinstance(exc, KeyboardInterrupt) else "failed"
        comparison["error"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        comparison["elapsed_s"] = time.monotonic() - started
        # base.run owns the exclusive directory. Never write into a colliding run.
        if out.is_dir() and (out / "summary.json").exists() and not isinstance(sys.exc_info()[1], FileExistsError):
            base._json_write(out / "comparison.json", comparison)
    return comparison


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    result = run(args.package, args.manifest_sha256, args.out)
    print(json.dumps({"status": result["status"], "decision": result["decision"], "run_directory": result["run_directory"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
