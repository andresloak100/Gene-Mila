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
