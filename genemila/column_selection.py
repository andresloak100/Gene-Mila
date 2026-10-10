"""Training-only column screening before an independently fitted ridge model.

The caller supplies only the current training fold. Evaluation rows and labels
are deliberately absent from this API. A fitted mask is never reused in CV.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Real
import warnings

import numpy as np

MAX_ITER = 20000
TOLERANCE = 1e-6


class ColumnSelectionError(ValueError):
    pass


def _finite_number(value) -> bool:
    if isinstance(value, bool) or not isinstance(value, Real):
        return False
    try:
        return math.isfinite(float(value))
    except (OverflowError, ValueError):
        return False


def validate_column_selection(config: dict) -> dict:
    """Validate an agent-visible configuration and return explicit defaults."""
    if not isinstance(config, dict):
        raise ColumnSelectionError("column_selection must be an object")
    if any(not isinstance(key, str) for key in config):
        raise ColumnSelectionError("column_selection keys must be strings")
    method = config.get("method")
    if method not in ("lasso", "elasticnet", "variance"):
        raise ColumnSelectionError("column_selection.method must be lasso, elasticnet, or variance")
    allowed = {"method"} if method == "variance" else {"method", "alpha", "max_iter"}
    if method == "elasticnet":
        allowed.add("l1_ratio")
    if set(config) - allowed:
        raise ColumnSelectionError(f"unknown column_selection keys: {sorted(set(config) - allowed)}")
    result = {"method": method}
    if method == "variance":
        return result
    alpha = config.get("alpha")
    if not _finite_number(alpha) or alpha <= 0:
        raise ColumnSelectionError("column_selection.alpha must be a positive finite number")
    max_iter = config.get("max_iter", 5000)
    if isinstance(max_iter, bool) or not isinstance(max_iter, int) or not 1 <= max_iter <= MAX_ITER:
        raise ColumnSelectionError(f"column_selection.max_iter must be an integer in [1, {MAX_ITER}]")
    result.update(alpha=float(alpha), max_iter=max_iter)
    if method == "elasticnet":
        ratio = config.get("l1_ratio", 0.5)
        if not _finite_number(ratio) or not 0 < ratio <= 1:
            raise ColumnSelectionError("column_selection.l1_ratio must be finite and in (0, 1]")
        result["l1_ratio"] = float(ratio)
    return result


@dataclass(frozen=True)
class ColumnSelection:
    mask: np.ndarray
    mean: np.ndarray
    scale: np.ndarray
    metadata: dict


def fit_column_selection(x: np.ndarray, y: np.ndarray, config: dict, *, seed: int = 0) -> ColumnSelection:
    """Fit a deterministic selector on finite raw training rows and a 1-D target."""
    from sklearn.exceptions import ConvergenceWarning
    from sklearn.linear_model import ElasticNet, Lasso

    config = validate_column_selection(config)
    x, y = np.asarray(x, dtype=np.float64), np.asarray(y, dtype=np.float64)
    if x.ndim != 2 or not all(x.shape):
        raise ColumnSelectionError("selector X must be a nonempty two-dimensional matrix")
    if y.ndim != 1 or len(y) != len(x):
        raise ColumnSelectionError("selector y must be one-dimensional with one target per training row")
    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
        raise ColumnSelectionError("selector training inputs must be finite")
    mean, scale = x.mean(axis=0), x.std(axis=0)
    if not np.all(np.isfinite(mean)) or not np.all(np.isfinite(scale)):
        raise ColumnSelectionError("selector training normalization is nonfinite")
    nonconstant = np.any(x != x[0], axis=0) & (scale > 0)
    if not np.any(nonconstant):
        raise ColumnSelectionError("column selection is empty: all training columns are constant")
    scale[~nonconstant] = 1.0
    mask = nonconstant.copy()
    metadata = {"config": config, "fit_scope": "training_rows_only", "seed": int(seed),
                "n_training_rows": len(x), "n_raw_features": x.shape[1],
                "constant_indices": np.flatnonzero(~nonconstant).tolist(), "converged": True}
    if config["method"] != "variance":
        normalized = (x[:, nonconstant] - mean[nonconstant]) / scale[nonconstant]
        if not np.all(np.isfinite(normalized)):
            raise ColumnSelectionError("selector standardized training matrix is nonfinite")
        kwargs = {"alpha": config["alpha"], "max_iter": config["max_iter"],
                  "tol": TOLERANCE, "fit_intercept": True, "random_state": seed, "selection": "cyclic"}
        selector = (Lasso(**kwargs) if config["method"] == "lasso" else
                    ElasticNet(l1_ratio=config["l1_ratio"], **kwargs))
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", ConvergenceWarning)
            selector.fit(normalized, y)
        if not np.all(np.isfinite(selector.coef_)) or not np.isfinite(selector.intercept_) or not np.isfinite(selector.dual_gap_):
            raise ColumnSelectionError("column selector produced nonfinite fitted values")
        if any(issubclass(w.category, ConvergenceWarning) for w in caught):
            raise ColumnSelectionError(f"{config['method']} column selector did not converge within {config['max_iter']} iterations")
        mask[nonconstant] = selector.coef_ != 0.0
        metadata.update(tolerance=TOLERANCE, n_iter=int(selector.n_iter_),
                        dual_gap=float(selector.dual_gap_), selector_intercept=float(selector.intercept_),
                        nonconstant_indices=np.flatnonzero(nonconstant).tolist(),
                        selector_coefficients=selector.coef_.tolist())
    if not np.any(mask):
        raise ColumnSelectionError("column selection is empty: no training-supported columns survived")
    metadata.update(selected_indices=np.flatnonzero(mask).tolist(), selected_mask=mask.tolist(),
                    n_selected_features=int(mask.sum()))
    return ColumnSelection(mask=mask, mean=mean, scale=scale, metadata=metadata)


def predict_from_artifact(artifact: dict, raw_x: np.ndarray, raw_columns: list[str]) -> np.ndarray:
    """Predict from a saved models.pkl payload without refitting the selector.

    Output has shape (models, rows). Raw features must use the saved source order;
    callers retain the public context and source bundle that produced them.
    """
    x = np.asarray(raw_x, dtype=np.float64)
    expected = artifact.get("raw_columns", artifact["columns"])
    if list(raw_columns) != list(expected) or x.ndim != 2 or x.shape[1] != len(expected):
        raise ColumnSelectionError("inference raw columns do not match the fitted schema")
    if not np.all(np.isfinite(x)):
        raise ColumnSelectionError("inference features must be finite")
    mask = np.asarray(artifact.get("selected_mask", [True] * len(expected)), dtype=bool)
    mean, scale = np.asarray(artifact["x_mean"]), np.asarray(artifact["x_std"])
    if mask.shape != (len(expected),) or mean.shape != (int(mask.sum()),) or scale.shape != mean.shape:
        raise ColumnSelectionError("saved column selection and normalization shapes differ")
    prediction = np.stack([m.predict((x[:, mask] - mean) / scale) for m in artifact["models"]])
    if not np.all(np.isfinite(prediction)):
        raise ColumnSelectionError("model produced nonfinite predictions")
    return prediction
