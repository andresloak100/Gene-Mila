import numpy as np
import pytest

from genemila.benchmark.evaluator import evaluate, is_better


def test_perfect_prediction():
    rng = np.random.default_rng(0)
    ctrl = rng.random(50)
    truth = ctrl + rng.normal(0, 1, (4, 50))
    m = evaluate(truth, truth, ctrl)["metrics"]
    assert m["rmse"] == pytest.approx(0)
    assert m["pearson_delta"] == pytest.approx(1)
    assert m["direction_acc_top"] == pytest.approx(1)


def test_unchanged_prediction_has_zero_delta_correlation():
    rng = np.random.default_rng(0)
    ctrl = rng.random(50)
    truth = ctrl + rng.normal(0, 1, (4, 50))
    m = evaluate(np.tile(ctrl, (4, 1)), truth, ctrl)["metrics"]
    assert m["pearson_delta"] == 0
    assert m["rmse"] > 0


def test_anticorrelated_is_negative_and_deterministic():
    rng = np.random.default_rng(1)
    ctrl = rng.random(30)
    truth = ctrl + rng.normal(0, 1, (3, 30))
    pred = ctrl - (truth - ctrl)
    a = evaluate(pred, truth, ctrl)
    b = evaluate(pred, truth, ctrl)
    assert a["metrics"]["pearson_delta"] == pytest.approx(-1)
    assert a == b


def test_invalid_predictions_rejected():
    ctrl = np.ones(5)
    with pytest.raises(ValueError):
        evaluate(np.full((2, 5), np.nan), np.ones((2, 5)), ctrl)
    with pytest.raises(ValueError):
        evaluate(np.ones((2, 4)), np.ones((2, 5)), ctrl)


def test_is_better():
    assert is_better(0.5, 0.4)
    assert not is_better(0.4, 0.5)
    assert is_better(0.1, None)
    assert is_better(0.1, 0.2, higher_is_better=False)


def test_r2_top_and_the_de_aware_selection_rule():
    """pearson_delta cannot see that a prediction is shrunk; the DE-aware rule can."""
    from genemila.benchmark import selection_score
    rng = np.random.default_rng(2)
    ctrl = rng.random(60)
    truth = ctrl + rng.normal(0, 1, (5, 60))
    shrunk = ctrl + 0.3 * (truth - ctrl)  # the right pattern at a third of the size
    m = evaluate(shrunk, truth, ctrl)["metrics"]
    assert m["pearson_delta"] == pytest.approx(1) and m["r2_top"] < 0.9
    assert m["primary"] == m["pearson_delta"] and m["selection_rule"] == "pearson_delta"
    de = evaluate(shrunk, truth, ctrl, selection="pearson_delta+r2_top")["metrics"]
    assert de["primary"] == pytest.approx(0.5 * (de["pearson_delta"] + de["r2_top"])) and de["primary"] < m["primary"]
    assert de["selection_rule"] == "pearson_delta+r2_top"
    exact = evaluate(truth, truth, ctrl, selection="pearson_delta+r2_top")["metrics"]
    assert exact["r2_top"] == pytest.approx(1) and exact["primary"] == pytest.approx(1)
    assert selection_score({"pearson_delta": 0.6, "r2_top": 0.8}, "pearson_delta+r2_top") == pytest.approx(0.7)
    with pytest.raises(ValueError, match="selection rule"):
        evaluate(truth, truth, ctrl, selection="nope")
