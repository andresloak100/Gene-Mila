"""Synthetic nested-learning boundaries, shared fits and stopped-run checks."""
import copy
import hashlib
import json

import numpy as np
import pytest

from genemila.features.api import FeatureContext
from tools import b1_nested_blend as blend

base = blend.base


@pytest.fixture
def synthetic(tmp_path):
    package = tmp_path / "package"
    public = package / "context"
    (public / "knowledge").mkdir(parents=True)
    genes = [f"G{i}" for i in range(16)]
    targets = {f"single_{i}": [genes[i]] for i in range(12)}
    targets.update({f"pair_{i}": [genes[i], genes[(i + 1) % 12]] for i in range(12)})
    perts = list(targets)
    control = np.array([np.arange(16) + 1., np.arange(16) + .5, np.arange(16) + 1.5])
    delta = np.random.default_rng(21).normal(size=(len(perts), 16)) * .2
    np.savez_compressed(public / "public.npz", genes=genes, control_cells=control, perts=perts,
                        train_perts=perts, train_means=control.mean(0) + delta)
    (public / "knowledge" / "targets.json").write_text(json.dumps(targets))
    script = '''import numpy as np
from genemila.features.api import Feature, register
import_draw = np.random.random()
calls = 0
@register
class Primed(Feature):
    name = "primed"
    def compute(self, ctx, perts, params):
        global calls
        calls += 1
        if list(perts) == ctx.train_perts:
            assert calls == 1
            assert np.random.random() == np.random.RandomState(params["seed"]).random_sample()
            ctx.cache["primed"] = True
        else:
            assert calls == 2 and ctx.cache.get("primed")
        out = np.zeros((len(perts), ctx.n_genes, 1))
        for i, p in enumerate(perts):
            _, delta = ctx.train_delta(exclude=p)
            out[i, :, 0] = delta.mean(0) + np.arange(ctx.n_genes) * .03
        return out
'''
    members = []
    for i, (experiment, alpha) in enumerate((("EXP_0681", 20000.), ("EXP_0729", .00198), ("EXP_0519", 300.))):
        plugins = package / "members" / str(i) / "plugins"
        plugins.mkdir(parents=True)
        (plugins / "primed.py").write_text(script)
        members.append({"experiment_id": experiment, "alpha": alpha, "seed": i + 1, "model_type": "ridge",
            "features": ["is_target", "mean_response", "primed"], "columns": ["is_target", "mean_response", "primed"],
            "feature_params": {"primed": {"seed": i + 1}}})
    return package, FeatureContext(public), {"members": members, "files_sha256": {}}


def poison(ctx, perts):
    changed = copy.copy(ctx)
    changed._train_delta = ctx._train_delta.copy()
    for pert in perts:
        changed._train_delta[ctx._train_pos[pert]] = np.arange(ctx.n_genes) * 1e8
    return changed


def test_closed_form_weight_clipping_zero_and_shape_checks():
    additive = np.array([[1., -1., 2.], [0., 4., 5.]])
    ensemble = additive + np.array([[2., 3., 1.], [1., -2., 4.]])
    fitted = blend.learn_weight(additive, ensemble, additive + .25 * (ensemble - additive))
    assert fitted["lambda"] == .25 and fitted["mse_blend"] == 0.
    assert fitted["mse_blend"] < min(fitted["mse_additive"], fitted["mse_fixed_ensemble"])
    assert blend.learn_weight(additive, ensemble, additive - (ensemble - additive))["lambda"] == 0.
    assert blend.learn_weight(additive, ensemble, additive + 2 * (ensemble - additive))["lambda"] == 1.
    zero = blend.learn_weight(additive, additive.copy(), ensemble)
    assert zero["lambda"] == 0. and zero["zero_denominator"] and zero["denominator"] == 0.
    with pytest.raises(ValueError, match="equal nonempty"):
        blend.learn_weight(additive, ensemble[:1], additive)
    with pytest.raises(ValueError, match="nonfinite"):
        blend.learn_weight(additive, ensemble * np.nan, additive)


def test_all_outer_hidden_responses_leave_weight_and_predictions_unchanged(synthetic):
    package, ctx, manifest = synthetic
    metadata = next(fold for fold in blend.memberships(ctx)["6"] if set(fold["hide"]) - set(fold["predict"]))
    assert set(metadata["hide"]) - set(metadata["predict"])
    expected_meta, poisoned_meta = copy.deepcopy(metadata), copy.deepcopy(metadata)
    expected, inner = blend.fit_outer(ctx, package, manifest["members"], expected_meta, blend.Budget())
    changed, changed_inner = blend.fit_outer(poison(ctx, metadata["hide"]), package, manifest["members"], poisoned_meta, blend.Budget())
    assert expected_meta["weight_fit"] == poisoned_meta["weight_fit"]
    for arm in blend.ARMS:
        np.testing.assert_array_equal(expected[arm], changed[arm])
    for name in inner:
        np.testing.assert_array_equal(inner[name], changed_inner[name])
    np.testing.assert_array_equal(expected["fixed_ensemble"], (expected["member_0"] + expected["member_1"]) / 2)
    np.testing.assert_array_equal(expected["candidate"], expected["additive"] + expected_meta["weight_fit"]["lambda"] * (expected["fixed_ensemble"] - expected["additive"]))


def test_inner_hide_union_and_predictions_exclude_hidden_responses(synthetic):
    package, ctx, manifest = synthetic
    meta = next(meta for meta in blend.memberships(ctx)["7"]
                if any(set(f["hide"]) - set(f["predict"]) for f in meta["inner_folds"]))
    fold = next(f for f in meta["inner_folds"] if set(f["hide"]) - set(f["predict"]))
    assert set(fold["hide"]) - set(fold["predict"])
    assert set(fold["hide_union"]) == set(meta["hide"]) | set(fold["hide"])
    assert not set(meta["hide"]).intersection(fold["train"])
    changed = poison(ctx, fold["hide_union"])
    _, expected = blend.fit_outer(ctx, package, manifest["members"], copy.deepcopy(meta), blend.Budget())
    _, poisoned = blend.fit_outer(changed, package, manifest["members"], copy.deepcopy(meta), blend.Budget())
    rows = [list(expected["perturbations"]).index(p) for p in fold["predict"]]
    for arm in ("member_0", "member_1", "fixed_ensemble", "additive"):
        np.testing.assert_array_equal(expected[arm][rows], poisoned[arm][rows])
    # Their responses are permitted weight-training truth, so weight invariance is not required.


def prepare_run(synthetic, monkeypatch):
    package, ctx, manifest = synthetic
    monkeypatch.setattr(base, "load_export", lambda *args: manifest)
    original_hash = base._hash
    monkeypatch.setattr(base, "_hash", lambda path: original_hash(path) if path.is_file() else hashlib.sha256(str(path).encode()).hexdigest())
    return package, ctx, manifest


def test_exact_120_shared_fits_prefit_provenance_and_all_inner_learning_replay(synthetic, monkeypatch, tmp_path):
    package, ctx, manifest = prepare_run(synthetic, monkeypatch)
    out = tmp_path / "run"
    original = base.fit_member
    calls = []
    ambient_seeds, ambient_cap = base.SEEDS, base.MAX_FITS

    def member(view, predict, plugins, spec, budget):
        config = json.loads((out / "config.json").read_text())
        assert config["outer_seeds"] == [6, 7, 8] and config["max_member_fits"] == 120
        assert config["gate"] == blend.GATE and len(config["folds"]) == 3
        assert "docs/B1_NESTED_BLEND_PLAN.md" in config["source_sha256"]
        assert "docs/results/b1_nested_blend_20261013/run_with_deadline.py" in config["source_sha256"]
        assert spec["seed"] in (1, 2)
        calls.append((spec["seed"], spec["alpha"], tuple(view.train_perts), tuple(predict)))
        return original(view, predict, plugins, spec, budget)

    monkeypatch.setattr(base, "fit_member", member)
    summary = blend.run(package, base.MANIFEST_SHA256, out)
    assert summary["status"] == "complete" and summary["fit_count"] == len(calls) == 120
    assert base.SEEDS == ambient_seeds and base.MAX_FITS == ambient_cap
    assert len(list((out / "inner_oof").glob("*.npz"))) == 15
    with np.load(out / "predictions.npz", allow_pickle=False) as saved:
        for repeat in summary["repeats"]:
            seed = repeat["seed"]
            fixed = (saved[f"seed_{seed}_member_0"] + saved[f"seed_{seed}_member_1"]) / 2
            np.testing.assert_array_equal(saved[f"seed_{seed}_fixed_ensemble"], fixed)
            assert sorted(p for fold in repeat["folds"] for p in fold["predict"]) == sorted(ctx.train_perts)
            for fold in repeat["folds"]:
                inner_path = out / fold["inner_oof_file"]
                assert base._hash(inner_path) == fold["inner_oof_sha256"]
                with np.load(inner_path, allow_pickle=False) as inner:
                    order = [str(p) for p in inner["perturbations"]]
                    assert order == fold["train"] == ctx.without_train(fold["hide"]).train_perts
                    _, truth = ctx.without_train(fold["hide"]).train_delta()
                    assert blend.learn_weight(inner["additive"], inner["fixed_ensemble"], truth) == fold["weight_fit"]
                rows = [ctx._train_pos[p] for p in fold["predict"]]
                additive = saved[f"seed_{seed}_additive"][rows]
                expected = additive + fold["weight_fit"]["lambda"] * (fixed[rows] - additive)
                np.testing.assert_array_equal(saved[f"seed_{seed}_candidate"][rows], expected)
    original_bytes = (out / "summary.json").read_bytes()
    with pytest.raises(FileExistsError):
        blend.run(package, base.MANIFEST_SHA256, out)
    assert (out / "summary.json").read_bytes() == original_bytes and len(calls) == 120


def test_failure_keeps_inner_arrays_and_partial_outer_member(synthetic, monkeypatch, tmp_path):
    package, _, _ = prepare_run(synthetic, monkeypatch)
    original = base.fit_member
    calls = 0

    def stopped(*args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 8:  # 6 inner fits plus first outer member survived
            raise RuntimeError("synthetic second outer member failure")
        return original(*args, **kwargs)

    monkeypatch.setattr(base, "fit_member", stopped)
    out = tmp_path / "stopped"
    with pytest.raises(RuntimeError, match="second outer"):
        blend.run(package, base.MANIFEST_SHA256, out)
    summary = json.loads((out / "summary.json").read_text())
    assert summary["status"] == "failed" and summary["fit_count"] == 7
    fold = summary["repeats"][0]["folds"][0]
    assert "weight_fit" in fold
    with np.load(out / fold["inner_oof_file"], allow_pickle=False) as inner:
        assert np.isfinite(inner["fixed_ensemble"]).all()
    with np.load(out / "predictions.npz", allow_pickle=False) as saved:
        assert np.isfinite(saved["seed_6_member_0"]).any()
        assert np.isnan(saved["seed_6_member_1"]).all()
        assert np.isnan(saved["seed_6_candidate"]).all()


def test_budget_and_timeout_preserve_failed_status(synthetic, monkeypatch, tmp_path):
    budget = blend.Budget(); budget.fits = 120
    with pytest.raises(RuntimeError, match="fit cap"):
        budget.fit()
    package, _, _ = prepare_run(synthetic, monkeypatch)
    monkeypatch.setattr(base, "fit_member", lambda *args, **kwargs: (_ for _ in ()).throw(TimeoutError("synthetic deadline")))
    out = tmp_path / "timed_out"
    with pytest.raises(TimeoutError, match="synthetic deadline"):
        blend.run(package, base.MANIFEST_SHA256, out)
    assert json.loads((out / "summary.json").read_text())["status"] == "timed_out"
    assert len(list((out / "inner_oof").glob("*.npz"))) == 1


def gate_rows(gains=(.1, .1, .1), changes=(0., 0., 0.), fixed_errors=(1., 1., 1.), additive_errors=(1., 1., 1.), top=None):
    top = top or tuple(f - g for f, g in zip(fixed_errors, gains))
    return [{"metrics": {"fixed_ensemble": {"mse": f, "mse_top": f, "pearson_delta": 0.},
                          "candidate": {"mse": f - g, "mse_top": t, "pearson_delta": c},
                          "additive": {"mse": a, "mse_top": a}}}
            for f, a, g, c, t in zip(fixed_errors, additive_errors, gains, changes, top)]


def test_gate_strict_primary_inclusive_pearson_and_ratio_of_means():
    assert blend.gate(gate_rows())["passed"]
    assert not blend.gate(gate_rows(gains=(0., .1, .1)))["checks"]["mse_gain_each_positive"]
    varied = blend.gate(gate_rows(gains=(.0001, .0001, .2)))
    assert not varied["checks"]["mse_gain_mean_above_sd"]
    assert varied["primary_mse_gain_mean_sd"]["sd"] == np.std(varied["primary_mse_gains"], ddof=1)
    assert blend.gate(gate_rows(changes=(-.01, .004, 0.)))["passed"]
    assert not blend.gate(gate_rows(changes=(-.01001, .005, 0.)))["checks"]["pearson_each_above_min"]
    assert not blend.gate(gate_rows(changes=(-.003, -.003, -.003)))["checks"]["pearson_mean_above_min"]
    ratios = blend.gate(gate_rows(fixed_errors=(3., 101., 101.), additive_errors=(1., 100., 100.), gains=(1., 2., 1.)))
    assert ratios["error_guardrails"]["mse_to_additive"]["ratio"] == 1.
    assert ratios["passed"]  # mean of per-seed ratios would wrongly fail
    assert blend.gate(gate_rows(top=(1.01, 1.01, 1.01)))["passed"]
    assert not blend.gate(gate_rows(top=(1.01001, 1.01001, 1.01001)))["passed"]
    with pytest.raises(ValueError, match="three completed"):
        blend.gate(gate_rows()[:2])


def test_parent_timeout_preserves_nested_checkpoint_arrays_and_exclusive_directory(tmp_path, monkeypatch):
    import importlib.util
    import subprocess
    source = blend.REPO / "docs/results/b1_nested_blend_20261013/run_with_deadline.py"
    spec = importlib.util.spec_from_file_location("nested_blend_deadline", source)
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)
    out = tmp_path / "deadline"
    checkpoint = {"status": "running", "fit_count": 8,
                  "repeats": [{"seed": 6, "folds": [{"weight_fit": {"lambda": .25}, "inner_oof_file": "inner.npz"}]}]}
    retained = {}

    def timeout(command, **kwargs):
        assert kwargs["timeout"] == 7200 and command[1].endswith("tools/b1_nested_blend.py")
        out.mkdir()
        base._json_write(out / "summary.json", checkpoint)
        base._save_arrays(out / "inner.npz", {"partial": np.ones((2, 3))})
        retained["bytes"] = (out / "inner.npz").read_bytes()
        raise subprocess.TimeoutExpired(command, 7200)

    monkeypatch.setattr(launcher.subprocess, "run", timeout)
    assert launcher.launch(tmp_path / "package", out) == 124
    saved = json.loads((out / "summary.json").read_text())
    assert saved["status"] == "timed_out" and saved["fit_count"] == 8
    assert saved["repeats"] == checkpoint["repeats"]
    assert saved["decision"] == "no promotion; original B1 unchanged"
    assert (out / "inner.npz").read_bytes() == retained["bytes"]
    unchanged = (out / "summary.json").read_bytes()
    with pytest.raises(FileExistsError):
        launcher.launch(tmp_path / "package", out)
    assert (out / "summary.json").read_bytes() == unchanged
