"""Deterministic, visible-data-only column pruning on caller-built fixed folds.

This module has no data loading, lab, oracle, or provider access. Each fold's
feature matrices must already have been built without its evaluation labels.
Rows are perturbation/gene pairs; evaluation targets retain their two-dimensional
(perturbations, genes) shape so scoring weights perturbations, not folds.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import math
import time
import warnings
from typing import Callable, Mapping, Sequence

import numpy as np


@dataclass(frozen=True)
class FoldMatrices:
    train_x: np.ndarray
    train_y: np.ndarray
    eval_x: np.ndarray
    eval_y: np.ndarray


@dataclass(frozen=True)
class CandidateResult:
    columns: tuple[int, ...]
    alpha: float
    score: float
    guardrails: Mapping[str, float] = field(default_factory=dict)
    # Coefficients are on the ORIGINAL input scale, in columns order, per fold.
    coefficients: tuple[np.ndarray, ...] = field(default_factory=tuple)
    intercepts: tuple[float, ...] = field(default_factory=tuple)
    alpha_scores: tuple[tuple[float, float], ...] = field(default_factory=tuple)

    @property
    def n_columns(self) -> int:
        return len(self.columns)


@dataclass(frozen=True)
class PruningResult:
    baseline: CandidateResult
    best_score: CandidateResult
    compact: CandidateResult | None
    pareto: tuple[CandidateResult, ...]
    evaluated: tuple[CandidateResult, ...]
    stop_reason: str
    elapsed_s: float


@dataclass(frozen=True)
class LassoCandidate:
    """A sparse fit audit. A zero coefficient is NOT evidence of no usefulness."""
    model: CandidateResult
    support_by_fold: tuple[tuple[int, ...], ...]
    support_union: tuple[int, ...]
    support_intersection: tuple[int, ...]
    selection_frequency: tuple[float, ...]
    converged: tuple[bool, ...]
    iterations: tuple[int, ...]
    dual_gaps: tuple[float, ...]
    eligible: bool


@dataclass(frozen=True)
class LassoAudit:
    best: LassoCandidate | None
    evaluated: tuple[LassoCandidate, ...]
    seed_subsets: tuple[tuple[int, ...], ...]
    stop_reason: str
    elapsed_s: float


@dataclass(frozen=True)
class _PreparedFold:
    gram: np.ndarray
    cross: np.ndarray
    eval_x: np.ndarray
    eval_y: np.ndarray
    mean: np.ndarray
    scale: np.ndarray
    target_mean: float
    n_train: int


def _matrix(x: np.ndarray, name: str) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    if x.ndim != 2 or not all(x.shape) or not np.all(np.isfinite(x)):
        raise ValueError(f"{name} must be a nonempty finite two-dimensional matrix")
    return x


def _prepare(folds: Sequence[FoldMatrices]) -> tuple[_PreparedFold, ...]:
    if not folds:
        raise ValueError("at least one fixed fold is required")
    prepared = []
    n_columns = n_genes = None
    for fold in folds:
        train = _matrix(fold.train_x, "train_x")
        evaluation = _matrix(fold.eval_x, "eval_x")
        target = np.asarray(fold.train_y, dtype=np.float64).reshape(-1)
        truth = _matrix(fold.eval_y, "eval_y")
        if len(target) != len(train) or not np.all(np.isfinite(target)):
            raise ValueError("train_y must have one finite target per training row")
        if truth.size != len(evaluation):
            raise ValueError("eval_y perturbation/gene shape must match eval_x rows")
        if train.shape[1] != evaluation.shape[1]:
            raise ValueError("train_x and eval_x must have the same columns")
        if n_columns is None:
            n_columns, n_genes = train.shape[1], truth.shape[1]
        if train.shape[1] != n_columns or truth.shape[1] != n_genes:
            raise ValueError("all folds must have matching columns and gene counts")
        mean, scale = train.mean(axis=0), train.std(axis=0)
        scale[scale == 0] = 1.0
        normalized = (train - mean) / scale
        target_mean = float(target.mean())
        prepared.append(_PreparedFold(
            normalized.T @ normalized, normalized.T @ (target - target_mean),
            (evaluation - mean) / scale, truth, mean, scale, target_mean, len(train)))
    return tuple(prepared)


def _columns(columns: Sequence[int], n_columns: int) -> tuple[int, ...]:
    columns = tuple(columns)
    if not columns or any(not isinstance(c, (int, np.integer)) for c in columns):
        raise ValueError("a subset must contain integer column indices")
    if len(set(columns)) != len(columns) or min(columns) < 0 or max(columns) >= n_columns:
        raise ValueError("column indices must be unique and in range")
    return tuple(sorted(int(c) for c in columns))


def _alphas(alphas: Sequence[float]) -> tuple[float, ...]:
    result = tuple(sorted(set(float(a) for a in alphas)))
    if not result or any(not math.isfinite(a) or a < 0 for a in result):
        raise ValueError("alphas must contain finite nonnegative penalties")
    return result


def _rank(candidate: CandidateResult) -> tuple:
    return (-candidate.score, candidate.n_columns, candidate.columns, candidate.alpha)


def _evaluate(prepared: Sequence[_PreparedFold], columns: tuple[int, ...],
              alphas: tuple[float, ...], score_fn: Callable,
              guardrail_fn: Callable | None) -> CandidateResult:
    truth = np.concatenate([f.eval_y for f in prepared], axis=0)
    candidates = []
    for alpha in alphas:
        predictions, coefficients, intercepts = [], [], []
        for fold in prepared:
            gram = fold.gram[np.ix_(columns, columns)].copy()
            cross = fold.cross[list(columns)]
            if alpha > 0:
                gram.flat[::len(columns) + 1] += alpha
                beta = np.linalg.solve(gram, cross)
            else:
                # A Gram solve needs a squared singular-value cutoff. Exact
                # redundant columns are allowed; no arbitrary column is dropped.
                eigenvalues, eigenvectors = np.linalg.eigh(gram)
                cutoff = np.finfo(float).eps * max(fold.n_train, len(columns))
                cutoff *= max(float(eigenvalues[-1]), 0.0)
                inv = np.zeros_like(eigenvalues)
                np.divide(1.0, eigenvalues, out=inv, where=eigenvalues > cutoff)
                beta = eigenvectors @ (inv * (eigenvectors.T @ cross))
            prediction = fold.eval_x[:, columns] @ beta + fold.target_mean
            if not np.all(np.isfinite(prediction)):
                raise ValueError("ridge produced nonfinite predictions")
            predictions.append(prediction.reshape(fold.eval_y.shape))
            raw_coef = beta / fold.scale[list(columns)]
            coefficients.append(raw_coef)
            intercepts.append(float(fold.target_mean - fold.mean[list(columns)] @ raw_coef))
        prediction = np.concatenate(predictions, axis=0)
        score = float(score_fn(truth, prediction))
        if not math.isfinite(score):
            raise ValueError("score_fn must return a finite score")
        guards = {} if guardrail_fn is None else {
            str(k): float(v) for k, v in guardrail_fn(truth, prediction).items()}
        if not all(math.isfinite(v) for v in guards.values()):
            raise ValueError("guardrail_fn must return finite metric values")
        candidates.append(CandidateResult(columns, alpha, score, guards,
                                          tuple(coefficients), tuple(intercepts)))
    best = min(candidates, key=_rank)
    return CandidateResult(best.columns, best.alpha, best.score, best.guardrails,
                           best.coefficients, best.intercepts,
                           tuple((c.alpha, c.score) for c in candidates))


def ridge_candidate(folds: Sequence[FoldMatrices], columns: Sequence[int], *,
                    alpha: float, score_fn: Callable,
                    guardrail_fn: Callable | None = None) -> CandidateResult:
    """Fit one penalty shared across all fixed folds; score concatenated predictions.

    Training columns are standardized separately within each fold. The fitted
    intercept is unpenalized, matching a standardized Ridge(fit_intercept=True).
    """
    prepared = _prepare(folds)
    return _evaluate(prepared, _columns(columns, len(prepared[0].mean)),
                     _alphas([alpha]), score_fn, guardrail_fn)


def exact_duplicate_groups(matrices: np.ndarray | Sequence[np.ndarray]) -> tuple[tuple[int, ...], ...]:
    """Exact equality across ALL supplied matrices; first index is the representative.

    Supply training and evaluation matrices from every fold when checking whether
    a feature is redundant throughout the prepared views. These are candidate
    groups only: pruning duplicate columns changes ridge regularization.
    """
    if isinstance(matrices, np.ndarray):
        matrices = [matrices]
    arrays = [_matrix(x, "matrix") for x in matrices]
    if not arrays or len({a.shape[1] for a in arrays}) != 1:
        raise ValueError("matrices must have the same nonzero number of columns")
    buckets: dict[bytes, list[list[int]]] = {}
    for j in range(arrays[0].shape[1]):
        digest = hashlib.sha256()
        for array in arrays:
            column = array[:, j].copy()
            column[column == 0] = 0.0  # signed zero compares equal
            digest.update(column.tobytes())
        bucket = buckets.setdefault(digest.digest(), [])
        for group in bucket:
            if all(np.array_equal(a[:, j], a[:, group[0]]) for a in arrays):
                group.append(j)
                break
        else:
            bucket.append([j])
    return tuple(sorted(tuple(g) for bucket in buckets.values() for g in bucket if len(g) > 1))


def correlated_column_pairs(x: np.ndarray, threshold: float = 0.999) -> tuple[tuple[int, int, float], ...]:
    """Return candidate pairs with |Pearson correlation| >= threshold; never prune them.

    Constant columns are excluded. Correlation alone is not equivalence, and
    every suggested deletion still needs refitting and visible evaluation.
    """
    if not math.isfinite(threshold) or not 0 <= threshold <= 1:
        raise ValueError("correlation threshold must be between zero and one")
    x = _matrix(x, "x")
    centered = x - x.mean(axis=0)
    norms = np.linalg.norm(centered, axis=0)
    unit = np.divide(centered, norms, out=np.zeros_like(centered), where=norms > 0)
    correlations = np.clip(unit.T @ unit, -1.0, 1.0)
    return tuple((i, j, float(correlations[i, j])) for i in range(x.shape[1])
                 for j in range(i + 1, x.shape[1]) if norms[i] > 0 and norms[j] > 0
                 and abs(correlations[i, j]) >= threshold)


def pareto_front(candidates: Sequence[CandidateResult]) -> tuple[CandidateResult, ...]:
    """Nondominated score/column-count candidates, ordered from smallest to largest."""
    frontier = []
    best_score = -math.inf
    for candidate in sorted(candidates, key=lambda c: (c.n_columns, *_rank(c))):
        if candidate.score > best_score:
            frontier.append(candidate)
            best_score = candidate.score
    return tuple(frontier)


def lasso_support_audit(folds: Sequence[FoldMatrices], *, alphas: Sequence[float],
                        score_fn: Callable, guardrail_fn: Callable | None = None,
                        max_iter: int = 10000, tol: float = 1e-4,
                        coefficient_threshold: float = 1e-10,
                        max_active_features: int | None = None,
                        time_budget_s: float | None = None) -> LassoAudit:
    """Fit shared-alpha Lasso models and propose supports for guarded Ridge refits.

    Every fold standardizes on its training rows only. Lasso's objective uses
    squared error divided by 2*n_train, so its alpha is NOT Ridge's alpha.
    A penalty is evaluated across every fixed fold before it can be selected.
    ``score_fn`` sees concatenated perturbation arrays, as in curate_columns.

    Support uses standardized coefficients above ``coefficient_threshold``.
    Union, intersection and >=50% fold-stability supports from converged fits
    become ``seed_subsets``. A nonempty support and, optionally, union size <=
    max_active_features are required for eligibility. Nonconverged models are
    retained for audit but cannot win or seed pruning. The soft time budget is
    checked between complete penalty evaluations; the first always finishes.

    Zero coefficients establish exclusion under this penalty and these folds,
    not failure of the biological feature. Correlated features can substitute
    for each other. A proposed support must still be refitted and pass the
    caller's accuracy/DE guards before deployment or a failure classification.
    """
    from sklearn.exceptions import ConvergenceWarning
    from sklearn.linear_model import Lasso

    start = time.monotonic()
    penalties = _alphas(alphas)
    if penalties[0] == 0:
        raise ValueError("Lasso alphas must be strictly positive")
    if not isinstance(max_iter, int) or max_iter < 1 or not math.isfinite(tol) or tol <= 0:
        raise ValueError("max_iter and tol must be positive")
    if not math.isfinite(coefficient_threshold) or coefficient_threshold < 0:
        raise ValueError("coefficient_threshold must be finite and nonnegative")
    if time_budget_s is not None and (not math.isfinite(time_budget_s) or time_budget_s <= 0):
        raise ValueError("time_budget_s must be positive and finite")
    prepared = _prepare(folds)
    n_columns = len(prepared[0].mean)
    if max_active_features is not None and (
            not isinstance(max_active_features, int) or not 1 <= max_active_features <= n_columns):
        raise ValueError("max_active_features must be within the input column count")
    normalized_train = [np.asfortranarray((f.train_x - p.mean) / p.scale)
                        for f, p in zip(folds, prepared)]
    centered_targets = [np.asarray(f.train_y).reshape(-1) - p.target_mean
                        for f, p in zip(folds, prepared)]
    truth = np.concatenate([p.eval_y for p in prepared], axis=0)
    records = []
    stop_reason = "grid_complete"
    for alpha in penalties:
        if records and time_budget_s is not None and time.monotonic() - start >= time_budget_s:
            stop_reason = "time_budget"
            break
        predictions, coefficients, intercepts = [], [], []
        supports, converged, iterations, dual_gaps = [], [], [], []
        for x, target, fold in zip(normalized_train, centered_targets, prepared):
            model = Lasso(alpha=alpha, fit_intercept=False, precompute=fold.gram,
                          max_iter=max_iter, tol=tol, selection="cyclic", copy_X=True)
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", ConvergenceWarning)
                model.fit(x, target)
            finite = np.all(np.isfinite(model.coef_)) and math.isfinite(float(model.dual_gap_))
            if not finite:
                raise ValueError("Lasso produced nonfinite coefficients or dual gap")
            converged.append(not any(issubclass(w.category, ConvergenceWarning) for w in caught))
            iterations.append(int(model.n_iter_))
            dual_gaps.append(float(model.dual_gap_))
            supports.append(tuple(np.flatnonzero(np.abs(model.coef_) > coefficient_threshold).tolist()))
            predictions.append((fold.eval_x @ model.coef_ + fold.target_mean).reshape(fold.eval_y.shape))
            raw_coef = model.coef_ / fold.scale
            coefficients.append(raw_coef)
            intercepts.append(float(fold.target_mean - fold.mean @ raw_coef))
        prediction = np.concatenate(predictions, axis=0)
        if not np.all(np.isfinite(prediction)):
            raise ValueError("Lasso produced nonfinite predictions")
        score = float(score_fn(truth, prediction))
        metrics = {} if guardrail_fn is None else {
            str(k): float(v) for k, v in guardrail_fn(truth, prediction).items()}
        if not math.isfinite(score) or not all(math.isfinite(v) for v in metrics.values()):
            raise ValueError("Lasso scoring and guardrail functions must return finite values")
        union = tuple(sorted(set().union(*map(set, supports))))
        intersection = tuple(sorted(set.intersection(*map(set, supports))))
        frequency = tuple(sum(j in support for support in supports) / len(supports)
                          for j in range(n_columns))
        eligible = bool(union) and all(converged) and (
            max_active_features is None or len(union) <= max_active_features)
        candidate = CandidateResult(tuple(range(n_columns)), alpha, score, metrics,
                                    tuple(coefficients), tuple(intercepts), ((alpha, score),))
        records.append(LassoCandidate(candidate, tuple(supports), union, intersection,
                                      frequency, tuple(converged), tuple(iterations),
                                      tuple(dual_gaps), eligible))
    eligible = [r for r in records if r.eligible]
    best = min(eligible, key=lambda r: (-r.model.score, len(r.support_union), r.model.alpha)) if eligible else None
    seeds = set()
    for record in eligible:
        seeds.update([record.support_union, record.support_intersection,
                      tuple(j for j, frequency in enumerate(record.selection_frequency) if frequency >= .5)])
    seeds.discard(())
    return LassoAudit(best, tuple(records), tuple(sorted(seeds, key=lambda s: (len(s), s))),
                      stop_reason, time.monotonic() - start)


def curate_columns(folds: Sequence[FoldMatrices], *, alphas: Sequence[float],
                   score_fn: Callable, initial_subsets: Sequence[Sequence[int]] = (),
                   epsilon: float = 0.0, max_candidates: int = 250,
                   time_budget_s: float | None = None, min_columns: int = 1,
                   guardrail_fn: Callable | None = None,
                   guardrail_tolerances: Mapping[str, tuple[str, float]] | None = None,
                   seed_order: str = "smallest") -> PruningResult:
    """Budgeted backward elimination with an untouched full-column reference.

    ``score_fn(truth, prediction)`` sees concatenated (perturbations, genes)
    arrays, never a mean of fold scores. Each subset chooses ONE alpha on these
    same fixed folds. Initial subsets (e.g. dropping a projection block or exact
    duplicates) are evaluated first in the supplied order. ``seed_order`` selects
    subsequent traversal: smallest column sets first (default), or the highest
    scoring evaluated seeds first ("best_score"). Under either traversal, each
    step follows the highest-scoring one-column deletion, including unfavorable
    intermediate steps. Only qualifying models are recommended at the end.

    ``max_candidates`` counts subsets, including the full baseline. The time
    limit is soft, checked between subsets; baseline preparation and its entire
    alpha grid always finish. ``evaluated`` retains each subset's winning alpha
    plus every alpha score. The best score is always kept separately.

    Compact candidates must score at least max(baseline, best_score - epsilon).
    Default epsilon=0 never sacrifices accuracy. Optional DE guards map names
    to ("max" or "min", absolute allowed degradation) relative to the baseline;
    metric names must appear in guardrail_fn's output. ``compact`` is None if
    no candidate satisfies BOTH accuracy and these optional guards.
    """
    start = time.monotonic()
    if seed_order not in ("smallest", "best_score"):
        raise ValueError("seed_order must be smallest or best_score")
    if not math.isfinite(epsilon) or epsilon < 0:
        raise ValueError("epsilon must be finite and nonnegative")
    if not isinstance(max_candidates, int) or max_candidates < 1:
        raise ValueError("max_candidates must be a positive integer")
    if time_budget_s is not None and (not math.isfinite(time_budget_s) or time_budget_s <= 0):
        raise ValueError("time_budget_s must be positive and finite")
    prepared = _prepare(folds)
    n_columns = len(prepared[0].mean)
    if not isinstance(min_columns, int) or not 1 <= min_columns <= n_columns:
        raise ValueError("min_columns must be within the input column count")
    penalties = _alphas(alphas)
    seeds = [_columns(c, n_columns) for c in initial_subsets]
    if any(len(s) < min_columns for s in seeds):
        raise ValueError("initial subsets must respect min_columns")
    guards = dict(guardrail_tolerances or {})
    for direction, tolerance in guards.values():
        if direction not in ("max", "min") or not math.isfinite(tolerance) or tolerance < 0:
            raise ValueError("guardrails need a max/min direction and nonnegative finite tolerance")
    if guards and guardrail_fn is None:
        raise ValueError("guardrail_tolerances require guardrail_fn")
    cache: dict[tuple[int, ...], CandidateResult] = {}
    stop_reason = "search_complete"

    def evaluate(columns):
        nonlocal stop_reason
        if columns in cache:
            return cache[columns]
        if cache and len(cache) >= max_candidates:
            stop_reason = "max_candidates"
            return None
        if cache and time_budget_s is not None and time.monotonic() - start >= time_budget_s:
            stop_reason = "time_budget"
            return None
        candidate = _evaluate(prepared, columns, penalties, score_fn, guardrail_fn)
        if not guards.keys() <= candidate.guardrails.keys():
            raise ValueError("guardrail_fn did not return every required metric")
        cache[columns] = candidate
        return candidate

    full = tuple(range(n_columns))
    baseline = evaluate(full)
    evaluated_seeds = [full]
    for seed in seeds:
        if evaluate(seed) is None:
            break
        evaluated_seeds.append(seed)
    order = (lambda c: (len(c), c)) if seed_order == "smallest" else (lambda c: _rank(cache[c]))
    for seed in sorted(set(evaluated_seeds), key=order):
        current = seed
        while len(current) > min_columns and stop_reason == "search_complete":
            children = []
            for column in current:
                child = evaluate(tuple(c for c in current if c != column))
                if child is None:
                    break
                children.append(child)
            if not children or stop_reason != "search_complete":
                break
            current = min(children, key=_rank).columns
    evaluated = tuple(cache.values())
    best = min(evaluated, key=_rank)
    threshold = max(baseline.score, best.score - epsilon)

    def qualifies(candidate):
        if candidate.score < threshold:
            return False
        for metric, (direction, tolerance) in guards.items():
            value, reference = candidate.guardrails[metric], baseline.guardrails[metric]
            if direction == "max" and value < reference - tolerance:
                return False
            if direction == "min" and value > reference + tolerance:
                return False
        return True

    eligible = [c for c in evaluated if qualifies(c)]
    compact = min(eligible, key=lambda c: (c.n_columns, *_rank(c))) if eligible else None
    return PruningResult(baseline, best, compact, pareto_front(evaluated), evaluated,
                         stop_reason, time.monotonic() - start)
