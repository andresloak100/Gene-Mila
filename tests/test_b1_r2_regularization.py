"""Synthetic alpha-only ablation, hidden-label boundary and run preservation."""
import copy
import hashlib
import json

import numpy as np
import pytest

from test_b1_development_diagnostic import synthetic  # shared synthetic fixture only
from tools import b1_r2_regularization as regularization

base = regularization.base


def metadata(ctx, seed=9):
    predict, hide = next((p, h) for p, h in base._folds(ctx, seed) if set(h) - set(p))
    assert set(hide) - set(predict)
    return base.fold_metadata(ctx, predict, hide, 0, set())


def test_variant_is_deep_copy_changing_alpha_only(synthetic):
    _, _, manifest = synthetic
    original = copy.deepcopy(manifest["members"][1])
    variant = regularization.regularized_spec(original)
    assert variant["alpha"] == 20000.
    assert {k: v for k, v in variant.items() if k != "alpha"} == {k: v for k, v in original.items() if k != "alpha"}
    variant["features"].append("synthetic_mutation")
    variant["feature_params"]["primed"]["seed"] = 100
    assert original == manifest["members"][1]


def test_r2_matrices_params_seeds_and_plugin_snapshot_are_identical(synthetic, monkeypatch):
    package, ctx, manifest = synthetic
    original = base.fit_member
    matrix = base.build_matrix
    specs, matrices = [], []

    def fit(view, predict, plugins, member, budget):
        specs.append((plugins, copy.deepcopy(member)))
        return original(view, predict, plugins, member, budget)

    def build(*args, **kwargs):
        result = matrix(*args, **kwargs)
        matrices.append((result[0].copy(), list(result[1])))
        return result

    monkeypatch.setattr(base, "fit_member", fit)
    monkeypatch.setattr(base, "build_matrix", build)
    untouched = copy.deepcopy(manifest)
    predictions = regularization.fit_outer(ctx, package, manifest["members"], metadata(ctx), base.Budget())
    assert manifest == untouched
    assert specs[1][0] == specs[2][0] == package / "members" / "1" / "plugins"
    assert specs[1][1]["seed"] == specs[2][1]["seed"] == 2
    assert specs[1][1]["alpha"] == .00198 and specs[2][1]["alpha"] == 20000.
    assert {k: v for k, v in specs[1][1].items() if k != "alpha"} == {k: v for k, v in specs[2][1].items() if k != "alpha"}
    for original_matrix, variant_matrix in ((matrices[2], matrices[4]), (matrices[3], matrices[5])):
        np.testing.assert_array_equal(original_matrix[0], variant_matrix[0])
        assert original_matrix[1] == variant_matrix[1]
    np.testing.assert_array_equal(predictions["fixed_ensemble"], (predictions["member_0"] + predictions["member_1"]) / 2)
    np.testing.assert_array_equal(predictions["candidate"], (predictions["member_0"] + predictions["regularized_member_1"]) / 2)


def test_full_hide_union_poisoning_cannot_change_any_arm(synthetic):
    package, ctx, manifest = synthetic
    meta = metadata(ctx)
    expected = regularization.fit_outer(ctx, package, manifest["members"], meta, base.Budget())
    poisoned = copy.copy(ctx)
    poisoned._train_delta = ctx._train_delta.copy()
    for pert in meta["hide"]:
        poisoned._train_delta[ctx._train_pos[pert]] = np.arange(ctx.n_genes) * 1e9
    actual = regularization.fit_outer(poisoned, package, manifest["members"], meta, base.Budget())
    for arm in regularization.ARMS:
        np.testing.assert_array_equal(expected[arm], actual[arm])


def prepare_run(synthetic, monkeypatch):
    package, ctx, manifest = synthetic
    monkeypatch.setattr(base, "load_export", lambda *args: manifest)
    original_hash = base._hash
    monkeypatch.setattr(base, "_hash", lambda path: original_hash(path) if path.is_file() else hashlib.sha256(str(path).encode()).hexdigest())
    return package, ctx, manifest


def test_exact_45_shared_fits_and_prefit_source_configuration(synthetic, monkeypatch, tmp_path):
    package, ctx, manifest = prepare_run(synthetic, monkeypatch)
    out = tmp_path / "run"
    original = base.fit_member
    calls = []
    original_seeds = base.SEEDS

    def fit(view, predict, plugins, member, budget):
        config = json.loads((out / "config.json").read_text())
        assert config["outer_seeds"] == [9, 10, 11] and config["max_ridge_fits"] == 45
        assert config["variant"]["alpha"] == 20000. and config["variant"]["seed"] == 2
        assert config["gate"] == regularization.GATE
        assert "docs/B1_R2_REGULARIZATION_PLAN.md" in config["source_sha256"]
        assert "docs/results/b1_r2_regularization_20261013/run_with_deadline.py" in config["source_sha256"]
        assert not any("nested_blend" in p for p in config["source_sha256"])
        calls.append((member["seed"], member["alpha"]))
        return original(view, predict, plugins, member, budget)

    monkeypatch.setattr(base, "fit_member", fit)
    summary = regularization.run(package, base.MANIFEST_SHA256, out)
    assert summary["status"] == "complete" and summary["fit_count"] == len(calls) == 45
    assert calls == [(1, 20000.), (2, .00198), (2, 20000.)] * 15
    assert base.SEEDS == original_seeds
    with np.load(out / "predictions.npz", allow_pickle=False) as saved:
        for repeat in summary["repeats"]:
            seed = repeat["seed"]
            assert sorted(p for fold in repeat["folds"] for p in fold["predict"]) == sorted(ctx.train_perts)
            np.testing.assert_array_equal(saved[f"seed_{seed}_candidate"],
                (saved[f"seed_{seed}_member_0"] + saved[f"seed_{seed}_regularized_member_1"]) / 2)
            np.testing.assert_array_equal(saved[f"seed_{seed}_fixed_ensemble"],
                (saved[f"seed_{seed}_member_0"] + saved[f"seed_{seed}_member_1"]) / 2)
    original_bytes = (out / "summary.json").read_bytes()
    with pytest.raises(FileExistsError):
        regularization.run(package, base.MANIFEST_SHA256, out)
    assert (out / "summary.json").read_bytes() == original_bytes and len(calls) == 45
    changes = [r["metrics"]["candidate"]["mse"] - r["metrics"]["fixed_ensemble"]["mse"] for r in summary["repeats"]]
    paired = summary["paired_differences_over_seeds"]["fixed_ensemble"]["candidate"]["mse"]
    assert paired["mean"] == np.mean(changes) and paired["sd"] == np.std(changes, ddof=1)


@pytest.mark.parametrize("failure,status", [(RuntimeError("variant failure"), "failed"),
                                          (TimeoutError("variant timeout"), "timed_out")])
def test_variant_failure_preserves_original_member_predictions(synthetic, monkeypatch, tmp_path, failure, status):
    package, _, _ = prepare_run(synthetic, monkeypatch)
    original = base.fit_member
    calls = 0

    def stopped(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 3:
            raise failure
        return original(*args, **kwargs)

    monkeypatch.setattr(base, "fit_member", stopped)
    out = tmp_path / "stopped"
    with pytest.raises(type(failure), match=str(failure)):
        regularization.run(package, base.MANIFEST_SHA256, out)
    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == status and summary["fit_count"] == 2
    with np.load(out / "predictions.npz", allow_pickle=False) as saved:
        assert np.isfinite(saved["seed_9_member_0"]).any() and np.isfinite(saved["seed_9_member_1"]).any()
        assert np.isnan(saved["seed_9_regularized_member_1"]).all()
        assert np.isnan(saved["seed_9_candidate"]).all()


def gate_rows(gains=(.1, .1, .1), changes=(0., 0., 0.), fixed_errors=(1., 1., 1.), additive_errors=(1., 1., 1.), top=None):
    top = top or tuple(f - g for f, g in zip(fixed_errors, gains))
    return [{"metrics": {"fixed_ensemble": {"mse": f, "mse_top": f, "pearson_delta": 0.},
                          "candidate": {"mse": f - g, "mse_top": t, "pearson_delta": c},
                          "additive": {"mse": a, "mse_top": a}}}
            for f, a, g, c, t in zip(fixed_errors, additive_errors, gains, changes, top)]


def test_gate_primary_and_correlation_boundaries_use_sample_sd_and_ratios_of_means():
    assert regularization.gate(gate_rows())["passed"]
    assert not regularization.gate(gate_rows(gains=(0., .1, .1)))["checks"]["mse_gain_each_positive"]
    varied = regularization.gate(gate_rows(gains=(.0001, .0001, .2)))
    assert not varied["checks"]["mse_gain_mean_above_sd"]
    assert varied["primary_mse_gain_mean_sd"]["sd"] == np.std(varied["primary_mse_gains"], ddof=1)
    assert regularization.gate(gate_rows(changes=(-.01, .004, 0.)))["passed"]
    assert not regularization.gate(gate_rows(changes=(-.01001, .005, 0.)))["checks"]["pearson_each_above_min"]
    assert not regularization.gate(gate_rows(changes=(-.003, -.003, -.003)))["checks"]["pearson_mean_above_min"]
    ratios = regularization.gate(gate_rows(fixed_errors=(3., 101., 101.), additive_errors=(1., 100., 100.), gains=(1., 2., 1.)))
    assert ratios["error_guardrails"]["mse_to_additive"]["ratio"] == 1. and ratios["passed"]
    assert regularization.gate(gate_rows(top=(1.01, 1.01, 1.01)))["passed"]
    assert not regularization.gate(gate_rows(top=(1.01001, 1.01001, 1.01001)))["passed"]
    with pytest.raises(ValueError, match="three completed"):
        regularization.gate(gate_rows()[:2])


def test_parent_timeout_preserves_fold_checkpoint_and_refuses_reuse(tmp_path, monkeypatch):
    import importlib.util
    import subprocess
    source = regularization.REPO / "docs/results/b1_r2_regularization_20261013/run_with_deadline.py"
    spec = importlib.util.spec_from_file_location("r2_regularization_deadline", source)
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    out = tmp_path / "deadline"
    checkpoint = {"status": "running", "fit_count": 2, "repeats": [{"seed": 9, "folds": [{"status": "running"}]}]}
    retained = {}

    def timeout(command, **kwargs):
        assert kwargs["timeout"] == 7200 and command[1].endswith("tools/b1_r2_regularization.py")
        out.mkdir()
        base._json_write(out / "summary.json", checkpoint)
        base._save_arrays(out / "predictions.npz", {"original_members": np.ones((2, 3))})
        retained["bytes"] = (out / "predictions.npz").read_bytes()
        raise subprocess.TimeoutExpired(command, 7200)

    monkeypatch.setattr(launcher.subprocess, "run", timeout)
    assert launcher.launch(tmp_path / "package", out) == 124
    saved = json.loads((out / "summary.json").read_text())
    assert saved["status"] == "timed_out" and saved["fit_count"] == 2 and saved["repeats"] == checkpoint["repeats"]
    assert (out / "predictions.npz").read_bytes() == retained["bytes"]
    unchanged = (out / "summary.json").read_bytes()
    with pytest.raises(FileExistsError):
        launcher.launch(tmp_path / "package", out)
    assert (out / "summary.json").read_bytes() == unchanged
