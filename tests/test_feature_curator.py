"""Pure array tests: no lab, oracle, campaign files, or provider calls."""

import numpy as np
import pytest

from genemila.feature_curator import (
    CandidateResult, FoldMatrices, correlated_column_pairs, curate_columns,
    exact_duplicate_groups, lasso_support_audit, pareto_front, ridge_candidate,
)


def negative_mse(truth, prediction):
    return -float(np.mean((truth - prediction) ** 2))


def folds_fixture():
    rng = np.random.default_rng(123)
    folds = []
    for n_train, n_eval in [(35, 2), (45, 3)]:
        x = rng.normal(size=(n_train, 3)) * [1, 20, .03] + [5, -7, 11]
        z = rng.normal(size=(n_eval * 4, 3)) * [1, 20, .03] + [5, -7, 11]
        weights = np.array([.7, -.05, 4.0])
        folds.append(FoldMatrices(x, x @ weights + 1.8, z, (z @ weights + 1.8).reshape(n_eval, 4)))
    return folds


def test_ridge_matches_fold_local_standardization_and_preserves_raw_coefficients():
    from sklearn.linear_model import Ridge
    folds = folds_fixture()
    result = ridge_candidate(folds, [0, 2], alpha=2.5, score_fn=negative_mse)
    predictions = []
    for fold, coefficient, intercept in zip(folds, result.coefficients, result.intercepts):
        x, z = fold.train_x[:, [0, 2]], fold.eval_x[:, [0, 2]]
        mu, sd = x.mean(0), x.std(0)
        model = Ridge(alpha=2.5).fit((x - mu) / sd, fold.train_y)
        expected = model.predict((z - mu) / sd)
        actual = z @ coefficient + intercept
        np.testing.assert_allclose(actual, expected, rtol=1e-11, atol=1e-11)
        predictions.append(actual.reshape(fold.eval_y.shape))
    assert result.score == pytest.approx(negative_mse(
        np.concatenate([f.eval_y for f in folds]), np.concatenate(predictions)))


def test_one_alpha_is_selected_globally_and_scoring_sees_all_perturbations():
    folds = folds_fixture()
    seen_shapes = []

    def score(truth, prediction):
        seen_shapes.append(truth.shape)
        return negative_mse(truth, prediction)

    result = curate_columns(folds, alphas=[100, .1, 3], score_fn=score, max_candidates=1)
    references = [ridge_candidate(folds, [0, 1, 2], alpha=a, score_fn=negative_mse)
                  for a in [.1, 3, 100]]
    winner = max(references, key=lambda c: c.score)
    assert result.baseline.alpha == winner.alpha
    assert result.baseline.score == pytest.approx(winner.score)
    assert set(seen_shapes) == {(5, 4)}  # unequal folds are not weighted equally
    assert len(result.evaluated) == 1
    assert result.stop_reason == "max_candidates"


def test_duplicates_across_all_views_and_correlations_are_only_suggestions():
    x = np.array([[0., -0., 2., 7.], [1., 1., 4., 7.], [2., 2., 6., 7.]])
    assert exact_duplicate_groups(x) == ((0, 1),)
    changed = x.copy()
    changed[0, 1] = 2
    assert exact_duplicate_groups([x, changed]) == ()
    pairs = correlated_column_pairs(x, .999)
    assert {(i, j) for i, j, _ in pairs} == {(0, 1), (0, 2), (1, 2)}
    assert not any(3 in (i, j) for i, j, _ in pairs)


def test_pruning_keeps_accuracy_best_and_only_compacts_at_exact_tie_by_default():
    folds = folds_fixture()
    # A deliberately constant score tests deterministic tie handling independent
    # of floating-point fitting noise or an assumed equivalent ridge penalty.
    result = curate_columns(folds, alphas=[1, 2], score_fn=lambda y, p: .6,
                            initial_subsets=[[0, 1]], max_candidates=12)
    assert result.baseline.columns == (0, 1, 2)
    assert result.compact.columns == (0,)
    assert result.compact.score >= result.baseline.score
    assert result.best_score.score == .6
    again = curate_columns(folds, alphas=[2, 1], score_fn=lambda y, p: .6,
                           initial_subsets=[[0, 1]], max_candidates=12)
    assert [(c.columns, c.alpha, c.score) for c in result.evaluated] == [
        (c.columns, c.alpha, c.score) for c in again.evaluated]


def test_epsilon_does_not_allow_degradation_below_full_baseline_and_guards_apply():
    folds = folds_fixture()
    result = curate_columns(folds, alphas=[.1, 100], score_fn=negative_mse,
                            epsilon=100, max_candidates=20,
                            guardrail_fn=lambda y, p: {"mse": -negative_mse(y, p)},
                            guardrail_tolerances={"mse": ("min", 0)})
    assert result.compact.score >= result.baseline.score
    assert result.compact.guardrails["mse"] <= result.baseline.guardrails["mse"]
    assert result.best_score.score == max(c.score for c in result.evaluated)
    with pytest.raises(ValueError, match="every required metric"):
        curate_columns(folds, alphas=[1], score_fn=negative_mse,
                       guardrail_fn=lambda y, p: {},
                       guardrail_tolerances={"mse": ("min", 0)})


def test_pareto_eliminates_equal_size_and_equal_score_dominated_candidates():
    a = CandidateResult((0,), 1, .5)
    b = CandidateResult((1,), 1, .4)
    c = CandidateResult((0, 1), 1, .5)
    d = CandidateResult((0, 1, 2), 1, .6)
    assert pareto_front([d, c, b, a]) == (a, d)


def test_invalid_arrays_and_subsets_fail_before_selection():
    folds = folds_fixture()
    with pytest.raises(ValueError, match="unique"):
        ridge_candidate(folds, [0, 0], alpha=1, score_fn=negative_mse)
    with pytest.raises(ValueError, match="nonnegative"):
        ridge_candidate(folds, [0], alpha=-1, score_fn=negative_mse)
    bad = FoldMatrices(folds[0].train_x, folds[0].train_y, folds[0].eval_x, np.ones((1, 3)))
    with pytest.raises(ValueError, match="shape"):
        curate_columns([bad], alphas=[1], score_fn=negative_mse)


def test_soft_time_budget_still_finishes_baseline(monkeypatch):
    import genemila.feature_curator as curator
    clock = iter([0., 2., 2., 2., 2.])
    monkeypatch.setattr(curator.time, "monotonic", lambda: next(clock))
    result = curate_columns(folds_fixture(), alphas=[1, 10], score_fn=negative_mse,
                            initial_subsets=[[0]], time_budget_s=1)
    assert len(result.evaluated) == 1 and result.baseline is result.best_score
    assert result.stop_reason == "time_budget"


def test_lasso_reports_shared_alpha_support_stability_and_raw_predictions():
    from sklearn.linear_model import Lasso
    folds = folds_fixture()
    audit = lasso_support_audit(folds, alphas=[.01, .1, 1], score_fn=negative_mse,
                               max_iter=10000, tol=1e-9)
    assert audit.best.model.score == max(r.model.score for r in audit.evaluated if r.eligible)
    assert len(audit.evaluated) == 3 and audit.seed_subsets
    for record in audit.evaluated:
        union, intersection = set(), set(range(3))
        for i, fold in enumerate(folds):
            mu, sd = fold.train_x.mean(0), fold.train_x.std(0)
            model = Lasso(alpha=record.model.alpha, max_iter=10000, tol=1e-9).fit(
                (fold.train_x - mu) / sd, fold.train_y)
            expected = model.predict((fold.eval_x - mu) / sd)
            actual = fold.eval_x @ record.model.coefficients[i] + record.model.intercepts[i]
            np.testing.assert_allclose(actual, expected, rtol=1e-8, atol=1e-8)
            union.update(record.support_by_fold[i])
            intersection.intersection_update(record.support_by_fold[i])
        assert set(record.support_union) == union
        assert set(record.support_intersection) == intersection
        assert all(f in (0., .5, 1.) for f in record.selection_frequency)


def test_nonconverged_lasso_is_audited_but_cannot_seed_or_win():
    audit = lasso_support_audit(folds_fixture(), alphas=[1e-10], score_fn=negative_mse,
                               max_iter=1, tol=1e-12)
    assert audit.best is None and not audit.seed_subsets
    assert not all(audit.evaluated[0].converged)
    assert not audit.evaluated[0].eligible


def test_lasso_support_cap_is_enforced_without_dropping_audit_records():
    audit = lasso_support_audit(folds_fixture(), alphas=[.0001], score_fn=negative_mse,
                               max_active_features=1)
    assert len(audit.evaluated[0].support_union) > 1
    assert audit.best is None and not audit.seed_subsets
    with pytest.raises(ValueError, match="strictly positive"):
        lasso_support_audit(folds_fixture(), alphas=[0], score_fn=negative_mse)


def test_seed_order_controls_traversal_under_budget_without_changing_baseline(monkeypatch):
    import genemila.feature_curator as curator
    folds = []
    for f in folds_fixture():
        folds.append(FoldMatrices(np.column_stack([f.train_x, np.zeros(len(f.train_x))]), f.train_y,
                                   np.column_stack([f.eval_x, np.zeros(len(f.eval_x))]), f.eval_y))
    scores = {(0, 1, 2, 3): .9, (0, 1): .6, (0, 1, 2): .95, (1, 2): .96, (0, 2): .94}

    def evaluate(prepared, columns, alphas, score_fn, guardrail_fn):
        return CandidateResult(columns, 1, scores.get(columns, .4))

    monkeypatch.setattr(curator, "_evaluate", evaluate)
    kwargs = dict(alphas=[1], score_fn=negative_mse, initial_subsets=[(0, 1), (0, 1, 2)], max_candidates=5)
    small = curate_columns(folds, **kwargs)
    strong = curate_columns(folds, **kwargs, seed_order="best_score")
    assert [r.columns for r in small.evaluated[-2:]] == [(1,), (0,)]
    assert [r.columns for r in strong.evaluated[-2:]] == [(1, 2), (0, 2)]
    assert small.baseline.columns == strong.baseline.columns == (0, 1, 2, 3)
    assert strong.best_score.score == .96 and strong.compact.score >= strong.baseline.score
    assert small.stop_reason == strong.stop_reason == "max_candidates"
    with pytest.raises(ValueError, match="seed_order"):
        curate_columns(folds, **kwargs, seed_order="unknown")
