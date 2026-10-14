"""Synthetic boundary, recipe-fidelity and stopped-run checks; no real bundle."""
import copy
import json
import sys

import numpy as np
import pytest

from genemila.features.api import FeatureContext
from genemila.features.builtin import AdditiveResponse
from genemila.features import registry
from tools import b1_development_diagnostic as diagnostic


@pytest.fixture
def synthetic(tmp_path):
    package = tmp_path / "package"
    public = package / "context"
    (public / "knowledge").mkdir(parents=True)
    genes = [f"G{i}" for i in range(8)]
    targets = {f"single_{i}": [genes[i]] for i in range(6)}
    targets.update({f"pair_{i}": [genes[i], genes[(i + 1) % 6]] for i in range(6)})
    perts = list(targets)
    control = np.array([np.arange(8) + 1., np.arange(8) + .3, np.arange(8) + 1.4])
    delta = np.random.default_rng(17).normal(size=(len(perts), 8)) * .2
    np.savez_compressed(public / "public.npz", genes=genes, control_cells=control, perts=perts,
                        train_perts=perts, train_means=control.mean(0) + delta)
    (public / "knowledge" / "targets.json").write_text(json.dumps(targets))
    # Module and context priming expose reuse or evaluation-first mistakes.
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
            draw = np.random.random()
            assert draw == np.random.RandomState(params["seed"]).random_sample()
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
    for i, (experiment, alpha) in enumerate((('EXP_0681', 20000.), ('EXP_0729', .00198), ('EXP_0519', 300.))):
        plugins = package / "members" / str(i) / "plugins"
        plugins.mkdir(parents=True)
        (plugins / "primed.py").write_text(script)
        members.append({"experiment_id": experiment, "alpha": alpha, "seed": i + 1,
            "model_type": "ridge", "features": ["is_target", "mean_response", "primed"],
            "columns": ["is_target", "mean_response", "primed"], "feature_params": {"primed": {"seed": i + 1}}})
    return package, FeatureContext(public), {"members": members, "files_sha256": {}}


def member_prediction(ctx, package, member, predict, hide):
    view = ctx.without_train(hide)
    return diagnostic.fit_member(view, predict, package / "members" / "0" / "plugins", member, diagnostic.Budget())


def test_all_outer_hidden_labels_cannot_reach_member_or_additive(synthetic):
    package, ctx, manifest = synthetic
    predict, hide = next((p, h) for p, h in diagnostic._folds(ctx, 0) if set(h) - set(p))
    expected = member_prediction(ctx, package, manifest["members"][0], predict, hide)
    additive = AdditiveResponse().compute(ctx.without_train(hide), predict, {})
    poisoned = copy.copy(ctx)
    poisoned._train_delta = ctx._train_delta.copy()
    for pert in hide:
        poisoned._train_delta[ctx._train_pos[pert]] = np.arange(ctx.n_genes) * 1e9
    np.testing.assert_array_equal(expected, member_prediction(poisoned, package, manifest["members"][0], predict, hide))
    np.testing.assert_array_equal(additive, AdditiveResponse().compute(poisoned.without_train(hide), predict, {}))


def test_fresh_modules_context_priming_seed_and_ambient_state(synthetic):
    package, ctx, manifest = synthetic
    predict, hide = diagnostic._folds(ctx, 1)[0]
    np.random.seed(981)
    state = np.random.get_state()
    expected_rng = np.random.RandomState(); expected_rng.set_state(state)
    names = set(registry.REGISTRY)
    modules = {key: value for key, value in sys.modules.items() if key.startswith("genemila_plugin_")}
    a = member_prediction(ctx, package, manifest["members"][0], predict, hide)
    b = member_prediction(ctx, package, manifest["members"][0], predict, hide)
    np.testing.assert_array_equal(a, b)
    assert set(registry.REGISTRY) == names
    assert {key: value for key, value in sys.modules.items() if key.startswith("genemila_plugin_")} == modules
    assert np.random.random() == expected_rng.random_sample()
    assert not ctx.cache and not ctx._feature_cache


def test_scaler_uses_training_rows_and_exact_column_order(synthetic, monkeypatch):
    package, ctx, manifest = synthetic
    predict, hide = diagnostic._folds(ctx, 2)[0]
    view = ctx.without_train(hide)
    n_train = len(view.train_perts) * ctx.n_genes
    train_x = np.column_stack((np.arange(n_train), np.full(n_train, 7.), np.arange(n_train) ** 2))
    pred_x = np.full((len(predict) * ctx.n_genes, 3), 1e6)
    member = manifest["members"][0]
    captured = {}

    def matrix(view, features, params, perts, timings, cache_dir):
        return (train_x.copy() if perts == view.train_perts else pred_x.copy()), member["columns"]

    class Model:
        def fit(self, x, y): captured["train"] = x
        def predict(self, x): captured["predict"] = x; return x[:, 0]

    monkeypatch.setattr(diagnostic, "build_matrix", matrix)
    monkeypatch.setattr(diagnostic, "make_model", lambda *args: Model())
    diagnostic.fit_member(view, predict, package / "members" / "0" / "plugins", member, diagnostic.Budget())
    sd = train_x.std(0); sd[sd == 0] = 1
    np.testing.assert_array_equal(captured["predict"], (pred_x - train_x.mean(0)) / sd)
    np.testing.assert_allclose(captured["train"].mean(0), 0, atol=1e-14)
    monkeypatch.setattr(diagnostic, "build_matrix", lambda *args, **kwargs: (train_x, ["wrong", "order", "here"]))
    with pytest.raises(ValueError, match="column order"):
        diagnostic.fit_member(view, predict, package / "members" / "0" / "plugins", member, diagnostic.Budget())


def test_metadata_coverage_alignment_and_known_single_strata(synthetic):
    package, ctx, _ = synthetic
    raw = {"genes": ["outside", "G3", "G1", "G0", "G2"], "measured": [True, False, True, True, True],
           "perts": {"G0": {"delta": [4, 9, 0, 0, 0]},  # constant profile remains usable
                     "G1": {"delta": [4, 9, 1, 2, 3], "n_cells": 0},
                     "G2": {"delta": [4, 9, None, 2, 3], "n_cells": 10},
                     "G3": {"delta": [4, 9, 1, 2, 3], "n_cells": 10},
                     "G4": {"delta": [1, 2]}, "G5": "malformed",
                     "G6": {"delta": [4, 9, "bad", 2, 3]},
                     "G7": {"delta": [4, 9, 1, 2, 3], "n_cells": "invalid"}}}
    path = package / "context" / "knowledge" / f"{diagnostic.KNOWLEDGE}.json"
    path.write_text(json.dumps(raw))
    assert diagnostic.usable_external_targets(ctx) == {"G0", "G3"}
    hide = ["single_0", "pair_0", "pair_5"]
    meta = diagnostic.fold_metadata(ctx, ["single_0", "pair_0", "pair_2", "single_2"], hide, 0, {"G0", "G3"})
    rows = {r["perturbation"]: r for r in meta["coverage"]}
    assert rows["single_0"]["known_singletons"] == 0
    assert rows["pair_0"]["known_singletons"] == 1
    assert rows["pair_0"]["external_coverage"] == "partial"
    assert rows["pair_2"]["external_coverage"] == "partial"
    assert rows["single_0"]["external_coverage"] == "all"
    assert rows["single_2"]["external_coverage"] == "none"
    assert all(r["known_singletons"] + r["unknown_contributions"] == len(r["targets"]) for r in rows.values())
    before = diagnostic._strata(meta["predict"], [meta])
    ctx._train_delta *= -1e6
    assert diagnostic.fold_metadata(ctx, meta["predict"], hide, 0, {"G0", "G3"}) == meta
    assert diagnostic._strata(meta["predict"], [meta]) == before
    ctx._targets["single_2"] = []
    unknown = diagnostic.fold_metadata(ctx, ["single_2"], ["single_2"], 0, {"G0", "G3"})
    assert unknown["coverage"][0]["external_coverage"] == "unknown"
    assert "external_unknown" in diagnostic._strata(["single_2"], [unknown])


def synthetic_run_setup(synthetic, monkeypatch):
    package, ctx, manifest = synthetic
    monkeypatch.setattr(diagnostic, "load_export", lambda *args: manifest)
    monkeypatch.setattr(diagnostic, "fixed_config", lambda *args: {"status": "fixed_before_fitting"})
    return package, ctx, manifest


def test_all_45_fits_partition_every_condition_and_equal_ensemble(synthetic, monkeypatch, tmp_path):
    package, ctx, manifest = synthetic_run_setup(synthetic, monkeypatch)
    summary = diagnostic.run(package, diagnostic.MANIFEST_SHA256, tmp_path / "run")
    assert summary["status"] == "complete" and summary["fit_count"] == 45
    with np.load(tmp_path / "run" / "predictions.npz", allow_pickle=False) as arrays:
        for repeat in summary["repeats"]:
            seed = repeat["seed"]
            assert sorted(p for fold in repeat["folds"] for p in fold["predict"]) == sorted(ctx.train_perts)
            np.testing.assert_array_equal(arrays[f"seed_{seed}_ensemble"],
                np.mean([arrays[f"seed_{seed}_member_{i}"] for i in range(3)], axis=0))
            counts = [repeat["strata"][g]["n_conditions"] for g in ("singleton", "pair")]
            assert sum(counts) == len(ctx.train_perts)
    expected = [r["metrics"]["ensemble"]["pearson_delta"] - r["metrics"]["additive"]["pearson_delta"] for r in summary["repeats"]]
    paired = summary["paired_differences_over_seeds"]["ensemble"]["pearson_delta"]
    assert paired["mean"] == np.mean(expected) and paired["sd"] == np.std(expected, ddof=1)


def test_exclusive_output_and_failure_preserve_completed_predictions(synthetic, monkeypatch, tmp_path):
    package, _, _ = synthetic_run_setup(synthetic, monkeypatch)
    original = diagnostic.make_model
    count = 0

    def model(*args):
        nonlocal count
        count += 1
        if count == 4:
            raise RuntimeError("synthetic failure after first fold")
        return original(*args)

    monkeypatch.setattr(diagnostic, "make_model", model)
    out = tmp_path / "stopped"
    with pytest.raises(RuntimeError, match="synthetic failure"):
        diagnostic.run(package, diagnostic.MANIFEST_SHA256, out)
    saved = json.loads((out / "summary.json").read_text())
    assert saved["status"] == "failed" and saved["fit_count"] == 3
    with np.load(out / "predictions.npz", allow_pickle=False) as arrays:
        assert np.isfinite(arrays["seed_0_ensemble"]).any()
        assert np.isnan(arrays["seed_0_ensemble"]).any()
    original_bytes = (out / "summary.json").read_bytes()
    with pytest.raises(FileExistsError):
        diagnostic.run(package, diagnostic.MANIFEST_SHA256, out)
    assert (out / "summary.json").read_bytes() == original_bytes


def test_deadline_and_fit_cap_are_enforced_before_new_fit(monkeypatch):
    budget = diagnostic.Budget()
    budget.fits = diagnostic.MAX_FITS
    with pytest.raises(RuntimeError, match="fit cap"):
        budget.fit()
    monkeypatch.setattr(diagnostic.time, "monotonic", lambda: budget.start + diagnostic.MAX_SECONDS)
    with pytest.raises(TimeoutError):
        budget.check()
