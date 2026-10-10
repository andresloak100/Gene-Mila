"""Small synthetic public bundles only: no evaluator, private files, or APIs."""
import json
import pickle

import numpy as np
import pytest

from genemila import pipeline
from genemila.column_selection import (
    ColumnSelectionError, fit_column_selection, predict_from_artifact,
    validate_column_selection,
)
from genemila.spec import ExperimentSpec, GuardrailViolation, config_hash, validate_spec


@pytest.mark.parametrize("method", ["lasso", "elasticnet"])
def test_sparse_screen_selects_signal_after_training_standardization(method):
    a = np.tile([-2., -1., 1., 2.], 20)
    b = np.tile([1., -2., 2., -1.], 20)
    x = np.column_stack((1000 * a + 23, b, np.ones(len(a))))
    selected = fit_column_selection(x, 3 * a + 7, {"method": method, "alpha": .1})
    assert selected.mask.tolist() == [True, False, False]
    assert selected.metadata["constant_indices"] == [2]
    assert selected.metadata["converged"] is True
    assert selected.metadata["selector_intercept"] == pytest.approx(7.)


def test_selector_configuration_hash_preserves_input_order():
    # Nearly identical columns may satisfy the sparse solver's convergence
    # tolerance with different supports depending on cyclic coordinate order.
    rng = np.random.default_rng(41)
    signal, noise = rng.normal(size=80), rng.normal(size=80)
    x = np.column_stack((signal + 1e-4 * noise, signal))
    config = {"method": "lasso", "alpha": .1}
    first = fit_column_selection(x, 3 * signal, config)
    reversed_fit = fit_column_selection(x[:, ::-1], 3 * signal, config)
    assert first.mask.sum() != reversed_fit.mask.sum()
    specs = [ExperimentSpec(hypothesis="Check the ordered synthetic input configuration.",
                            scientific_rationale="Different sparse supports need distinct candidate identities.",
                            feature_set=names, hyperparameters={"column_selection": config})
             for names in (["a", "b"], ["b", "a"])]
    sources = {"a": "source-a", "b": "source-b"}
    assert config_hash(specs[0], sources, "fixture") != config_hash(specs[1], sources, "fixture")
    for spec in specs:
        spec.hyperparameters = {}
    assert config_hash(specs[0], sources, "fixture") == config_hash(specs[1], sources, "fixture")


@pytest.mark.parametrize("config", [
    None, [], {}, {"method": "unknown"}, {"method": "lasso"},
    {"method": "lasso", "alpha": True}, {"method": "lasso", "alpha": "1"},
    {"method": "lasso", "alpha": 0}, {"method": "lasso", "alpha": -1},
    {"method": "lasso", "alpha": float("nan")}, {"method": "lasso", "alpha": float("inf")},
    {"method": "lasso", "alpha": 10 ** 400}, {"method": "variance", 1: 2, "extra": 3},
    {"method": "lasso", "alpha": .1, "max_iter": True},
    {"method": "lasso", "alpha": .1, "max_iter": 1.5},
    {"method": "lasso", "alpha": .1, "max_iter": 0},
    {"method": "lasso", "alpha": .1, "max_iter": 20001},
    {"method": "elasticnet", "alpha": .1, "l1_ratio": 0},
    {"method": "elasticnet", "alpha": .1, "l1_ratio": 1.01},
    {"method": "elasticnet", "alpha": .1, "l1_ratio": True},
    {"method": "elasticnet", "alpha": .1, "l1_ratio": float("nan")},
    {"method": "variance", "alpha": .1}, {"method": "variance", "cv_seed": 11},
    {"method": "lasso", "alpha": .1, "cv_folds": 2},
])
def test_configuration_rejects_invalid_values_and_extra_keys(config):
    with pytest.raises(ColumnSelectionError):
        validate_column_selection(config)


@pytest.mark.parametrize("x,y", [
    (np.ones(3), np.ones(3)), (np.empty((0, 2)), np.empty(0)),
    (np.empty((2, 0)), np.ones(2)), (np.ones((3, 2)), np.ones((3, 1))),
    (np.ones((3, 2)), np.ones(2)), (np.array([[1., np.inf], [2., 3.]]), np.ones(2)),
    (np.array([[1., 0.], [2., 3.]]), np.array([1., np.nan])),
])
def test_training_shapes_and_nonfinite_values_fail(x, y):
    with pytest.raises(ColumnSelectionError):
        fit_column_selection(x, y, {"method": "variance"})


def test_empty_and_unconverged_selections_fail_explicitly():
    with pytest.raises(ColumnSelectionError, match="empty"):
        fit_column_selection(np.ones((10, 3)), np.arange(10.), {"method": "variance"})
    with pytest.raises(ColumnSelectionError, match="empty"):
        fit_column_selection(np.arange(20.).reshape(10, 2), np.arange(10.),
                             {"method": "lasso", "alpha": 1e8})
    rng = np.random.default_rng(12)
    x = rng.normal(size=(80, 12))
    x[:, 1:] += x[:, :1]
    y = x @ np.arange(12.) + rng.normal(size=80)
    with pytest.raises(ColumnSelectionError, match="did not converge"):
        fit_column_selection(x, y, {"method": "lasso", "alpha": 1e-10, "max_iter": 1})


def test_nonfinite_selector_fit_fails(monkeypatch):
    class BrokenSelector:
        def __init__(self, **kwargs):
            pass

        def fit(self, x, y):
            self.coef_ = np.full(x.shape[1], np.nan)
            self.intercept_, self.dual_gap_ = 0., 0.
            return self

    monkeypatch.setattr("sklearn.linear_model.Lasso", BrokenSelector)
    with pytest.raises(ColumnSelectionError, match="nonfinite fitted"):
        fit_column_selection(np.arange(20.).reshape(10, 2), np.arange(10.),
                             {"method": "lasso", "alpha": .1})


def public_fixture(root, *, changed_pert=None, changed_evaluation=False):
    """Write only a tiny public interface, directly: no private bundle exists."""
    root.mkdir()
    public, plugins = root / "public", root / "plugins"
    (public / "knowledge").mkdir(parents=True)
    plugins.mkdir()
    perts = [f"p{i}" for i in range(7)]
    genes = [f"g{i}" for i in range(4)]
    signal = np.array([-2., -1., 1., 2.])
    noise = np.array([1., -2., 2., -1.])
    special = np.array([2., -1., -1., 2.])
    x = np.zeros((7, 4, 4))
    x[:, :, 0], x[:, :, 1], x[:, :, 2] = signal, noise, 1.
    x[0, :, 3] = special
    y = np.tile(3 * signal, (6, 1))
    y[0] += 50 * special
    if changed_pert is not None:
        i = perts.index(changed_pert)
        x[i] *= 50
        y[i] += np.array([17., -25., 31., -42.])
    if changed_evaluation:
        x[6] = 10000 * np.arange(16.).reshape(4, 4)
    np.savez(public / "public.npz", genes=np.array(genes), perts=np.array(perts),
             train_perts=np.array(perts[:6]), control_cells=np.zeros((5, 4)), train_means=y)
    (public / "manifest.json").write_text(json.dumps({"name": "synthetic_public", "split_id": "fixture"}))
    (public / "knowledge/targets.json").write_text(json.dumps({p: [genes[i % 4]] for i, p in enumerate(perts)}))
    (public / "knowledge/fixture_values.json").write_text(json.dumps(dict(zip(perts, x.tolist()))))
    (plugins / "fixture_columns.py").write_text('''import numpy as np
from genemila.features.api import Feature, register
@register
class FixtureColumns(Feature):
    name = "fixture_columns"
    dim = 4
    def compute(self, ctx, perts, params):
        values = ctx.knowledge("fixture_values")
        return np.array([values[p] for p in perts])
''')
    return public, plugins, x, y


def pipeline_spec(selection=True):
    hp = {"alpha": .5, "cv_folds": 3, "cv_seed": 0}
    if selection:
        hp["column_selection"] = {"method": "lasso", "alpha": .1}
    return {"feature_set": ["fixture_columns"], "model_type": "ridge", "hyperparameters": hp, "seed": 0}


def test_cv_refits_masks_and_held_fold_changes_cannot_affect_its_fit(tmp_path):
    public, plugins, _, _ = public_fixture(tmp_path / "first")
    first = pipeline.run(pipeline_spec(), public, plugins, tmp_path / "out1")
    fold = next(f for f in first["cv_column_selection"] if "p0" in f["eval_perts"])
    # Column 3 exists only for p0: visible to the full fit, constant in this fold.
    assert first["selected_mask"] == [True, False, False, True]
    assert fold["selected_mask"] == [True, False, False, False]
    assert fold["n_training_rows"] == 4 * 4
    public2, plugins2, _, _ = public_fixture(tmp_path / "changed", changed_pert="p0")
    second = pipeline.run(pipeline_spec(), public2, plugins2, tmp_path / "out2")
    same_fold = second["cv_column_selection"][fold["fold_index"]]
    assert same_fold == fold  # diagnostics, mask, coefficients and training membership all identical
    old = np.load(tmp_path / "out1/cv.npz")
    new = np.load(tmp_path / "out2/cv.npz")
    # The other held-out perturbation has unchanged features and receives the
    # same prediction, despite changed features AND labels for its fold peer.
    peer = next(p for p in fold["eval_perts"] if p != "p0")
    row = list(old["perts"]).index(peer)
    np.testing.assert_array_equal(old["delta"][:, row], new["delta"][:, row])


def test_final_selection_ignores_nontraining_rows_and_artifact_reproduces_prediction(tmp_path):
    public, plugins, x, _ = public_fixture(tmp_path / "first")
    out = tmp_path / "out"
    result = pipeline.run(pipeline_spec(), public, plugins, out)
    public2, plugins2, _, _ = public_fixture(tmp_path / "changed", changed_evaluation=True)
    changed = pipeline.run(pipeline_spec(), public2, plugins2, tmp_path / "out_changed")
    assert result["column_selection"] == changed["column_selection"]
    assert result["cv_column_selection"] == changed["cv_column_selection"]
    assert result["n_features"] == 2 and result["n_raw_features"] == 4
    assert result["retained_feature_set"] == ["fixture_columns"]
    artifact = pickle.loads((out / "models.pkl").read_bytes())
    prediction = predict_from_artifact(artifact, x[6:].reshape(4, 4), result["raw_columns"])
    saved = np.load(out / "predictions.npz")
    np.testing.assert_allclose(prediction.reshape(saved["delta"].shape), saved["delta"], rtol=1e-6, atol=1e-6)
    assert artifact["columns"] == result["columns"]
    assert artifact["selected_mask"] == result["selected_mask"]
    assert artifact["x_mean"].shape == artifact["x_std"].shape == (2,)
    assert len(result["coefficients"][0]["coef"]) == 2
    with pytest.raises(ColumnSelectionError, match="schema"):
        predict_from_artifact(artifact, x[6:].reshape(4, 4), list(reversed(result["raw_columns"])))


def test_retained_predictors_remain_distinct_from_required_source_dependencies(tmp_path):
    public, plugins, _, _ = public_fixture(tmp_path / "fixture")
    (plugins / "fixture_proxy.py").write_text('''from genemila.features.api import Feature, register
@register
class FixtureProxy(Feature):
    name = "fixture_proxy"
    dependencies = ["fixture_columns"]
    def compute(self, ctx, perts, params):
        return ctx.feature("fixture_columns", perts)[:, :, :1]
''')
    spec = pipeline_spec()
    spec["feature_set"] = ["fixture_proxy"]
    spec["hyperparameters"]["column_selection"] = {"method": "variance"}
    result = pipeline.run(spec, public, plugins, tmp_path / "out")
    assert result["retained_feature_set"] == ["fixture_proxy"]
    assert result["retained_feature_sources"] == ["fixture_columns", "fixture_proxy"]
    assert result["retained_dependency_only_sources"] == ["fixture_columns"]
    assert result["n_features"] == result["n_raw_features"] == 1


def test_absent_selector_preserves_legacy_ridge_predictions_and_columns(tmp_path):
    public, plugins, x, y = public_fixture(tmp_path / "fixture")
    result = pipeline.run(pipeline_spec(selection=False), public, plugins, tmp_path / "out")
    from sklearn.linear_model import Ridge
    train = x[:6].reshape(24, 4)
    mean, scale = train.mean(axis=0), train.std(axis=0)
    scale[scale == 0] = 1
    model = Ridge(alpha=.5).fit((train - mean) / scale, y.reshape(-1))
    expected = model.predict((x[6:].reshape(4, 4) - mean) / scale)
    saved = np.load(tmp_path / "out/predictions.npz")
    np.testing.assert_array_equal(saved["delta"].reshape(-1), expected.astype(np.float32))
    assert result["columns"] == result["raw_columns"]
    assert result["n_features"] == result["n_raw_features"] == 4
    assert result["column_selection"] is None and result["cv_column_selection"] == []


def test_spec_allows_bounded_selection_but_not_agent_cv_overrides():
    limits = {"cpu_limit_s": 600, "ram_limit_mb": 4096, "timeout_s": 300}
    spec = ExperimentSpec(hypothesis="Sparse columns should remove irrelevant predictors.",
                          scientific_rationale="Select using training rows and refit the response model.",
                          feature_set=["is_target"], hyperparameters={"column_selection": {"method": "variance"}})
    assert validate_spec(spec, {"is_target"}, limits) == []
    for option in ("cv_folds", "cv_seed"):
        spec.hyperparameters[option] = 2
        with pytest.raises(GuardrailViolation, match="unknown hyperparameter"):
            validate_spec(spec, {"is_target"}, limits)
        del spec.hyperparameters[option]
    spec.model_type = "lasso"
    with pytest.raises(GuardrailViolation, match="downstream ridge"):
        validate_spec(spec, {"is_target"}, limits)
