"""Metrics published by other perturbation-prediction systems, so our numbers
can be put next to theirs.

CellForge (arXiv 2508.02276, Table 1): MSE, PCC and R^2 between predicted and
true mean expression per perturbation, over all genes and over the top-20 DE
genes of the true response (MSE_DE, PCC_DE, R2_DE); mean over perturbations.

VCWorld (ICLR 2026): two classification tasks over (perturbation, gene) pairs.
DE: is the gene differentially expressed (Wilcoxon, BH-adjusted p <= 0.05,
|log2FC| >= 0.25)? DIR: for truly DE genes, is it up- or down-regulated?
Reported with accuracy, precision, recall, F1, AUROC and AUPRC, pooled over
pairs. A mean-expression model answers both through its predicted log2 fold
change: |log2FC| >= 0.25 means "DE" (|log2FC| is the ranking score) and the
sign gives the direction.

Ground-truth DE genes come from `reference.build` on the held-out cells.
"""

from __future__ import annotations

import numpy as np

from .reference import DE_LOGFC, log2_fc


def _pcc(a, b) -> float:
    a, b = a - a.mean(), b - b.mean()
    den = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / den) if den > 0 else 0.0


def _r2(truth, pred) -> float:
    ss_tot = ((truth - truth.mean()) ** 2).sum()
    return float(1 - ((truth - pred) ** 2).sum() / ss_tot) if ss_tot > 0 else 0.0


def cellforge(pred: np.ndarray, truth: np.ndarray, top_de: np.ndarray) -> dict:
    rows = []
    for i in range(truth.shape[0]):
        t, p, k = truth[i], pred[i], top_de[i]
        rows.append([np.mean((t - p) ** 2), _pcc(p, t), _r2(t, p),
                     np.mean((t[k] - p[k]) ** 2), _pcc(p[k], t[k]), _r2(t[k], p[k])])
    m = np.mean(rows, axis=0)
    return dict(zip(("cellforge_mse", "cellforge_pcc", "cellforge_r2",
                     "cellforge_mse_de", "cellforge_pcc_de", "cellforge_r2_de"), map(float, m)))


def _binary(prefix: str, y: np.ndarray, yhat: np.ndarray, score: np.ndarray) -> dict:
    from sklearn.metrics import average_precision_score, roc_auc_score
    tp = float(np.sum(y & yhat))
    prec = tp / max(1.0, float(yhat.sum()))
    rec = tp / max(1.0, float(y.sum()))
    out = {f"{prefix}_accuracy": float(np.mean(y == yhat)), f"{prefix}_precision": prec,
           f"{prefix}_recall": rec, f"{prefix}_f1": 2 * prec * rec / (prec + rec) if prec + rec else 0.0,
           f"{prefix}_auroc": None, f"{prefix}_auprc": None}
    if 0 < y.sum() < y.size:
        out[f"{prefix}_auroc"] = float(roc_auc_score(y, score))
        out[f"{prefix}_auprc"] = float(average_precision_score(y, score))
    return out


def vcworld(pred_delta: np.ndarray, ref: dict, rows: list[int]) -> dict:
    """pred_delta: predicted (perturbed - control) mean log1p expression for ref['perts'][rows].

    The prediction is anchored on the same held-out controls the true fold changes use."""
    cm = ref["control_mean"][None, :]
    lfc = log2_fc(np.clip(cm + pred_delta, 0, None), cm)
    de = ref["de"][rows].astype(bool)
    out = _binary("vcworld_de", de.ravel(), (np.abs(lfc) >= DE_LOGFC).ravel(), np.abs(lfc).ravel())
    up = (ref["direction"][rows] > 0)[de]
    out.update(_binary("vcworld_dir", up, (lfc > 0)[de], lfc[de]))
    out["vcworld_n_de_pairs"] = int(de.sum())
    return out


def score(pred: np.ndarray, truth: np.ndarray, perts: list[str], ref: dict | None,
          control_mean: np.ndarray) -> dict:
    """All comparable metrics for predicted/true mean expression in `perts` order ({} without a reference).
    control_mean is the public control mean the predictions are relative to."""
    if ref is None:
        return {}
    idx = {p: i for i, p in enumerate(ref["perts"])}
    keep = [i for i, p in enumerate(perts) if p in idx]
    if not keep:
        return {}
    rows = [idx[perts[i]] for i in keep]
    pred, truth = np.asarray(pred, dtype=np.float64)[keep], np.asarray(truth, dtype=np.float64)[keep]
    return {**cellforge(pred, truth, ref["top_de"][rows]), **vcworld(pred - control_mean, ref, rows)}
