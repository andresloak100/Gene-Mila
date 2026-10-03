"""Deterministic evaluation of perturbation predictions.

All metrics are computed per perturbation and averaged. "delta" means
expression minus the control mean, which is the quantity that actually carries
perturbation information; raw-expression correlations are reported too but are
dominated by baseline expression.
"""

from __future__ import annotations

import numpy as np

from . import PRIMARY_METRIC, TOP_DE


def _pearson(a: np.ndarray, b: np.ndarray) -> float:
    a = a - a.mean()
    b = b - b.mean()
    den = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / den) if den > 0 else 0.0


def evaluate(pred: np.ndarray, truth: np.ndarray, control_mean: np.ndarray, perts: list[str] | None = None,
             top_de: int = TOP_DE) -> dict:
    """pred, truth: (n_perts, n_genes) expression. Returns metrics + diagnostics."""
    pred = np.asarray(pred, dtype=np.float64)
    truth = np.asarray(truth, dtype=np.float64)
    if pred.shape != truth.shape:
        raise ValueError(f"prediction shape {pred.shape} != truth shape {truth.shape}")
    if not np.all(np.isfinite(pred)):
        raise ValueError("predictions contain NaN or infinite values")
    d_pred = pred - control_mean
    d_true = truth - control_mean
    err = pred - truth

    per_pert = []
    for i in range(truth.shape[0]):
        top = np.argsort(-np.abs(d_true[i]))[:top_de]
        per_pert.append({
            "pearson_delta": _pearson(d_pred[i], d_true[i]),
            "pearson_delta_top": _pearson(d_pred[i, top], d_true[i, top]),
            "direction_acc_top": float(np.mean(np.sign(d_pred[i, top]) == np.sign(d_true[i, top]))),
            "mse_top": float(np.mean(err[i, top] ** 2)),
            "pearson_expr": _pearson(pred[i], truth[i]),
        })
    metrics = {
        "rmse": float(np.sqrt(np.mean(err ** 2))),
        "mae": float(np.mean(np.abs(err))),
        "mse": float(np.mean(err ** 2)),
    }
    for key in per_pert[0]:
        metrics[key] = float(np.mean([p[key] for p in per_pert]))
    metrics["primary"] = metrics[PRIMARY_METRIC]

    # Diagnostics: where the errors are. Safe to show agents (aggregates only).
    names = perts or [str(i) for i in range(len(per_pert))]
    order = np.argsort([p["pearson_delta"] for p in per_pert])
    expr_q = np.quantile(control_mean, [0.25, 0.5, 0.75])
    bins = np.digitize(control_mean, expr_q)
    diagnostics = {
        "worst_perturbations": [{"pert": names[i], "pearson_delta": round(per_pert[i]["pearson_delta"], 3)}
                                for i in order[:5]],
        "best_perturbations": [{"pert": names[i], "pearson_delta": round(per_pert[i]["pearson_delta"], 3)}
                               for i in order[::-1][:3]],
        "rmse_by_control_expression_quartile": [
            round(float(np.sqrt(np.mean(err[:, bins == b] ** 2))), 4) for b in range(4)
        ],
        "mean_abs_true_delta": round(float(np.mean(np.abs(d_true))), 4),
        "mean_abs_pred_delta": round(float(np.mean(np.abs(d_pred))), 4),
        "delta_scale_ratio": round(float(np.mean(np.abs(d_pred)) / max(1e-12, np.mean(np.abs(d_true)))), 3),
    }
    return {"metrics": metrics, "diagnostics": diagnostics, "per_perturbation": dict(zip(names, per_pert))}


def is_better(a: float | None, b: float | None, higher_is_better: bool = True) -> bool:
    if a is None:
        return False
    if b is None:
        return True
    return a > b if higher_is_better else a < b
