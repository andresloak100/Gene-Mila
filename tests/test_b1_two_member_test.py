"""Synthetic fixed-composition, prospective config and stopped-run checks."""
from types import SimpleNamespace
import hashlib
import json

import numpy as np
import pytest

from tools import b1_two_member_test as comparison

base = comparison.base


@pytest.fixture
def shared(tmp_path, monkeypatch):
    package = tmp_path / "package"
    package.mkdir()
    perts, genes = [f"p{i}" for i in range(4)], [f"G{i}" for i in range(6)]
    truth = np.random.default_rng(19).normal(size=(4, 6))
    control = np.arange(6) + 1.
    ctx = SimpleNamespace(train_perts=perts, genes=genes, n_genes=6, control_mean=control,
                          train_delta=lambda: (perts, truth))
    manifest = {"files_sha256": {}, "members": [{"identity": "fixed synthetic receipt"}]}
    called, source_reads, arrays = [], [], {"perturbations": np.asarray(perts)}
    original_hash = base._hash

    def source_hash(path):
        source_reads.append(str(path))
        return original_hash(path) if path.is_file() else hashlib.sha256(str(path).encode()).hexdigest()

    def fake_run(package, pin, out):
        out.mkdir(exist_ok=False)
        config = base.fixed_config(package, pin, manifest, ctx, {})
        base._json_write(out / "config.json", config)
        # Simulated fits happen only after the candidate configuration is written.
        saved = json.loads((out / "config.json").read_text())
        assert saved["composition_comparison"]["candidate_weights"] == [.5, .5, 0.]
        assert saved["outer_seeds"] == [3, 4, 5]
        repeats = []
        for seed in base.SEEDS:
            rng = np.random.default_rng(seed)
            members = [truth + rng.normal(0, scale, truth.shape) for scale in (.1, .2, 2.)]
            ensemble, additive = np.mean(members, axis=0), truth * .3 + .4
            for i, values in enumerate(members):
                arrays[f"seed_{seed}_member_{i}"] = values
            arrays[f"seed_{seed}_ensemble"], arrays[f"seed_{seed}_additive"] = ensemble, additive
            metrics = {"ensemble": base.score_development(ensemble, truth, control, perts),
                       "additive": base.score_development(additive, truth, control, perts)}
            strata = {}
            for name, indices in (("singleton", [0, 1]), ("pair", [2, 3])):
                names = [perts[i] for i in indices]
                strata[name] = {"perturbations": names, "n_conditions": len(indices), "metrics": {
                    "ensemble": base.score_development(ensemble[indices], truth[indices], control, names),
                    "additive": base.score_development(additive[indices], truth[indices], control, names)}}
            repeats.append({"seed": seed, "metrics": metrics, "strata": strata})
            called.extend([seed] * 15)
        summary = {"status": "complete", "scored_training_perturbations": perts, "repeats": repeats, "fit_count": len(called)}
        base._save_arrays(out / "predictions.npz", arrays)
        base._json_write(out / "summary.json", summary)
        return summary

    monkeypatch.setattr(base, "run", fake_run)
    monkeypatch.setattr(base, "_hash", source_hash)
    monkeypatch.setattr(base, "FeatureContext", lambda *args, **kwargs: ctx)
    monkeypatch.setattr(base, "make_model", lambda *args: pytest.fail("wrapper must perform no extra fits"))
    return SimpleNamespace(package=package, out=tmp_path / "run", ctx=ctx, called=called,
                           source_reads=source_reads, arrays=arrays)


def test_candidate_averages_shared_arrays_and_reuses_exactly_45_fits(shared):
    seeds, config = base.SEEDS, base.fixed_config
    result = comparison.run(shared.package, base.MANIFEST_SHA256, shared.out)
    assert result["status"] == "complete" and len(shared.called) == 45
    assert shared.called == [3] * 15 + [4] * 15 + [5] * 15
    assert base.SEEDS == seeds and base.fixed_config is config
    with np.load(shared.out / "candidate_predictions.npz", allow_pickle=False) as saved:
        for seed, repeat in zip(comparison.SEEDS, result["repeats"]):
            expected = (shared.arrays[f"seed_{seed}_member_0"] + shared.arrays[f"seed_{seed}_member_1"]) / 2
            np.testing.assert_array_equal(saved[f"seed_{seed}_candidate"], expected)
            assert repeat["metrics"]["candidate"] == base.score_development(expected, shared.ctx.train_delta()[1], shared.ctx.control_mean, shared.ctx.train_perts)
    config = json.loads((shared.out / "config.json").read_text())
    assert config["max_ridge_fits"] == 45
    assert config["composition_comparison"]["gate"] == comparison.GATE
    assert config["composition_comparison"]["fold_seeds"] == [3, 4, 5]
    for name in ("tools/b1_two_member_test.py", "docs/B1_TWO_MEMBER_PLAN.md",
                 "docs/results/b1_two_member_test_20261013/run_with_deadline.py", "docs/B1_DIAGNOSTIC_PLAN.md"):
        assert name in config["source_sha256"]
    gains = [r["metrics"]["candidate"]["pearson_delta"] - r["metrics"]["baseline"]["pearson_delta"] for r in result["repeats"]]
    aggregate = result["paired_differences_over_seeds"]["baseline"]["pearson_delta"]
    assert aggregate["mean"] == np.mean(gains) and aggregate["sd"] == np.std(gains, ddof=1)
    assert all(result["strata_over_seeds"][group]["n_seeds"] == 3 for group in ("singleton", "pair"))


def test_baseline_artifacts_stay_exact_and_colliding_output_is_untouched(shared):
    comparison.run(shared.package, base.MANIFEST_SHA256, shared.out)
    with np.load(shared.out / "predictions.npz", allow_pickle=False) as saved:
        for name, values in shared.arrays.items():
            np.testing.assert_array_equal(saved[name], values)
    summary = (shared.out / "summary.json").read_bytes()
    candidate = (shared.out / "comparison.json").read_bytes()
    with pytest.raises(FileExistsError):
        comparison.run(shared.package, base.MANIFEST_SHA256, shared.out)
    assert (shared.out / "summary.json").read_bytes() == summary
    assert (shared.out / "comparison.json").read_bytes() == candidate
    assert len(shared.called) == 45


@pytest.mark.parametrize("exception,status", [(RuntimeError("stopped baseline"), "failed"),
                                              (TimeoutError("deadline"), "timed_out")])
def test_exception_restores_base_globals_and_preserves_baseline(shared, monkeypatch, exception, status):
    seeds, config = base.SEEDS, base.fixed_config

    def stopped(package, pin, out):
        out.mkdir()
        base._json_write(out / "summary.json", {"status": status, "retained": True})
        base._save_arrays(out / "predictions.npz", {"partial": np.ones((2, 3))})
        raise exception

    monkeypatch.setattr(base, "run", stopped)
    with pytest.raises(type(exception), match=str(exception)):
        comparison.run(shared.package, base.MANIFEST_SHA256, shared.out)
    assert base.SEEDS == seeds and base.fixed_config is config
    assert json.loads((shared.out / "summary.json").read_text()) == {"status": status, "retained": True}
    assert json.loads((shared.out / "comparison.json").read_text())["status"] == status
    with np.load(shared.out / "predictions.npz", allow_pickle=False) as saved:
        np.testing.assert_array_equal(saved["partial"], np.ones((2, 3)))


def test_scoring_failure_keeps_candidate_predictions_and_original_summary(shared, monkeypatch):
    original_run = base.run
    original_score = base.score_development

    def fitted(*args):
        summary = original_run(*args)
        monkeypatch.setattr(base, "score_development", lambda *args: (_ for _ in ()).throw(ValueError("score failure")))
        return summary

    monkeypatch.setattr(base, "run", fitted)
    with pytest.raises(ValueError, match="score failure"):
        comparison.run(shared.package, base.MANIFEST_SHA256, shared.out)
    assert json.loads((shared.out / "summary.json").read_text())["status"] == "complete"
    assert json.loads((shared.out / "comparison.json").read_text())["status"] == "failed"
    assert (shared.out / "candidate_predictions.npz").is_file()
    monkeypatch.setattr(base, "score_development", original_score)


def gate_rows(gains, baseline_errors=(1., 1., 1.), candidate_errors=None):
    candidate_errors = candidate_errors or baseline_errors
    return [{"metrics": {"baseline": {"pearson_delta": 0., "mse": b, "mse_top": b},
                         "candidate": {"pearson_delta": g, "mse": c, "mse_top": c}}}
            for g, b, c in zip(gains, baseline_errors, candidate_errors)]


def test_gate_uses_strict_boundaries_sample_sd_and_ratio_of_means():
    assert comparison.gate(gate_rows([.002, .002, .002]))["passed"] is False
    varied = comparison.gate(gate_rows([.0001, .0001, .1]))
    assert varied["paired_gain_mean_sd"]["sd"] == np.std([.0001, .0001, .1], ddof=1)
    assert varied["checks"]["mean_gain_above_threshold"] is False
    assert comparison.gate(gate_rows([0., .02, .02]))["checks"]["all_gains_positive"] is False
    ratios = comparison.gate(gate_rows([.02] * 3, (1., 100., 100.), (2., 99., 100.)))
    assert ratios["error_guardrails"]["mse"]["ratio"] == 1.
    assert ratios["passed"] is True  # average of individual ratios would exceed 1.01
    assert comparison.gate(gate_rows([.02] * 3, candidate_errors=(1.01, 1.01, 1.01)))["passed"] is True
    assert comparison.gate(gate_rows([.02] * 3, candidate_errors=(1.01001, 1.01001, 1.01001)))["passed"] is False
    with pytest.raises(ValueError, match="three completed"):
        comparison.gate(gate_rows([.02, .02]))


@pytest.mark.parametrize("baseline_complete", [True, False])
def test_parent_timeout_preserves_completed_baseline_and_marks_comparison(tmp_path, monkeypatch, baseline_complete):
    import importlib.util
    import subprocess
    source = comparison.REPO / "docs/results/b1_two_member_test_20261013/run_with_deadline.py"
    spec = importlib.util.spec_from_file_location("two_member_deadline", source)
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    out = tmp_path / "new"
    baseline = {"status": "complete" if baseline_complete else "running", "fit_count": 45 if baseline_complete else 4}
    original = json.dumps(baseline).encode()

    def timeout(*args, **kwargs):
        assert kwargs["timeout"] == 7200
        out.mkdir()
        (out / "summary.json").write_bytes(original)
        (out / "comparison.json").write_text('{"status":"running"}')
        raise subprocess.TimeoutExpired(args[0], 7200)

    monkeypatch.setattr(launcher.subprocess, "run", timeout)
    assert launcher.launch(tmp_path / "package", out) == 124
    if baseline_complete:
        assert (out / "summary.json").read_bytes() == original
    else:
        assert json.loads((out / "summary.json").read_text())["status"] == "timed_out"
    assert json.loads((out / "comparison.json").read_text())["status"] == "timed_out"
