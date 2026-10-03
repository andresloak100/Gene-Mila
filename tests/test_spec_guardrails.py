import pytest

from genemila.spec import ExperimentSpec, GuardrailViolation, PLUGIN_DIR, validate_spec

KNOWN = {"control_mean", "mean_response", "is_target", "coexpr"}
LIMITS = {"cpu_limit_s": 600, "ram_limit_mb": 4096, "timeout_s": 300}


def spec(**kw):
    base = dict(hypothesis="Co-expression with the target predicts response.",
                scientific_rationale="Genes in the same module move together after knockout.",
                kind="config", feature_set=["control_mean", "mean_response"])
    base.update(kw)
    return ExperimentSpec(**base)


def test_valid_config_spec():
    assert validate_spec(spec(), KNOWN, LIMITS) == []


def test_new_feature_rules():
    good = spec(kind="new_feature", proposed_feature={"name": "newf"}, feature_set=["mean_response", "newf"],
                allowed_files=[f"{PLUGIN_DIR}/newf.py"])
    validate_spec(good, KNOWN, LIMITS)
    with pytest.raises(GuardrailViolation):
        validate_spec(spec(kind="new_feature", proposed_feature={"name": "newf"}, feature_set=["newf"],
                           allowed_files=["genemila/benchmark/evaluator.py"]), KNOWN, LIMITS)
    with pytest.raises(GuardrailViolation):  # existing name
        validate_spec(spec(kind="new_feature", proposed_feature={"name": "coexpr"}, feature_set=["coexpr"],
                           allowed_files=[f"{PLUGIN_DIR}/coexpr.py"]), KNOWN, LIMITS)


@pytest.mark.parametrize("text", [
    "Use the validation 2 labels to calibrate", "train on hidden labels", "modify the evaluator to weight genes",
    "re-split the data so hard perturbations are in train", "peek at query-only perturbations",
])
def test_cheating_specs_rejected(text):
    with pytest.raises(GuardrailViolation):
        validate_spec(spec(hypothesis=text + " to improve the score."), KNOWN, LIMITS)


def test_missing_hypothesis_rejected():
    with pytest.raises(GuardrailViolation):
        validate_spec(spec(hypothesis="x"), KNOWN, LIMITS)


def test_compute_limits_and_models():
    with pytest.raises(GuardrailViolation):
        validate_spec(spec(timeout_s=10_000), KNOWN, LIMITS)
    with pytest.raises(GuardrailViolation):
        validate_spec(spec(model_type="xgboost"), KNOWN, LIMITS)
    with pytest.raises(GuardrailViolation):
        validate_spec(spec(hyperparameters={"n_estimators": 5}), KNOWN, LIMITS)


def test_config_cannot_change_code_or_use_unknown_features():
    with pytest.raises(GuardrailViolation):
        validate_spec(spec(allowed_files=[f"{PLUGIN_DIR}/x.py"]), KNOWN, LIMITS)
    with pytest.raises(GuardrailViolation):
        validate_spec(spec(feature_set=["mystery"]), KNOWN, LIMITS)


def test_multiple_simultaneous_changes():
    parent = {"feature_set_json": ["control_mean"], "model_type": "ridge", "feature_params_json": {}}
    flags = validate_spec(spec(feature_set=["control_mean", "mean_response", "is_target"]), KNOWN, LIMITS, parent)
    assert any(f.startswith("multiple_changes") for f in flags)
    with pytest.raises(GuardrailViolation):
        validate_spec(spec(feature_set=["mean_response", "is_target", "coexpr"], model_type="lasso"),
                      KNOWN, LIMITS, parent)
