"""Ground-truth differential-expression reference for held-out perturbations.

Built from the private held-out cells (perturbed cells vs. the held-out control
sample) once per dataset, and used by the comparable metrics:

* top-k DE genes per perturbation, as in GEARS/CellForge: scanpy's default
  `rank_genes_groups` (Welch t-test against control, ranked by |score|),
  optionally excluding genes that are zero in every perturbed cell
  ("non-dropout").
* DE labels and directions per (perturbation, gene), as in VCWorld: Wilcoxon
  rank-sum test against control, Benjamini-Hochberg adjusted p <= 0.05 and
  |log2 fold change| >= 0.25, with scanpy's fold-change definition.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

DE_PADJ = 0.05
DE_LOGFC = 0.25
TOP_K = 20


def log2_fc(mean_a: np.ndarray, mean_b: np.ndarray) -> np.ndarray:
    """scanpy's logfoldchanges for log1p data: log2((expm1(mean_a)+eps) / (expm1(mean_b)+eps))."""
    return np.log2((np.expm1(mean_a) + 1e-9) / (np.expm1(mean_b) + 1e-9))


def _bh(p: np.ndarray) -> np.ndarray:
    n = p.size
    order = np.argsort(p)
    ranked = p[order] * n / np.arange(1, n + 1)
    adj = np.minimum.accumulate(ranked[::-1])[::-1]
    out = np.empty_like(adj)
    out[order] = np.clip(adj, 0, 1)
    return out


def _welch_t(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    ma, mb = a.mean(0), b.mean(0)
    va, vb = a.var(0, ddof=1), b.var(0, ddof=1)
    se = np.sqrt(va / a.shape[0] + vb / b.shape[0])
    with np.errstate(divide="ignore", invalid="ignore"):
        t = (ma - mb) / se
    return np.nan_to_num(t, nan=0.0, posinf=0.0, neginf=0.0)


def build(X, labels: np.ndarray, top_k: int = TOP_K, non_dropout: bool = False) -> dict:
    """X: cells x genes (log-normalised), labels: 'control' or the perturbation per cell."""
    from scipy.stats import mannwhitneyu
    import scipy.sparse as sp
    X = X.toarray() if sp.issparse(X) else np.asarray(X)
    X = X.astype(np.float64)
    ctrl = X[labels == "control"]
    perts = [p for p in dict.fromkeys(labels.tolist()) if p != "control"]
    top, de, direction, logfc, padj = [], [], [], [], []
    for p in perts:
        cells = X[labels == p]
        t = _welch_t(cells, ctrl)
        score = np.abs(t)
        if non_dropout:
            score = np.where((cells != 0).any(0), score, -1.0)
        top.append(np.argsort(-score, kind="stable")[:top_k])
        lfc = log2_fc(cells.mean(0), ctrl.mean(0))
        varies = (cells.max(0) > cells.min(0)) | (ctrl.max(0) > ctrl.min(0))
        pv = np.ones(X.shape[1])
        if varies.any():
            pv[varies] = mannwhitneyu(cells[:, varies], ctrl[:, varies], axis=0, alternative="two-sided").pvalue
        pa = _bh(np.nan_to_num(pv, nan=1.0))
        de.append((pa <= DE_PADJ) & (np.abs(lfc) >= DE_LOGFC))
        direction.append(np.sign(lfc).astype(np.int8))
        logfc.append(lfc)
        padj.append(pa)
    return {"perts": np.array(perts), "top_de": np.array(top, dtype=np.int64), "de": np.array(de),
            "direction": np.array(direction), "logfc": np.array(logfc, dtype=np.float32),
            "padj": np.array(padj, dtype=np.float32), "control_mean": ctrl.mean(0),
            "top_k": top_k, "non_dropout": non_dropout}


def save(ref: dict, path: Path) -> None:
    np.savez_compressed(path, **{k: np.asarray(v) for k, v in ref.items()})


def load(data_dir: Path, part: str) -> dict | None:
    """The reference saved with the bundle, else built from the held-out cells, else None."""
    data_dir = Path(data_dir)
    path = data_dir / "private" / f"{part}_de.npz"
    if path.exists():
        z = np.load(path, allow_pickle=False)
        ref = {k: z[k] for k in z.files}
        ref["perts"] = [str(p) for p in ref["perts"]]
        return ref
    cells = data_dir / "private" / f"{part}_cells.npz"
    if not cells.exists():
        return None
    import scipy.sparse as sp
    labels = np.load(data_dir / "private" / f"{part}_cells_labels.npy", allow_pickle=False).astype(str)
    ref = build(sp.load_npz(cells), labels)
    ref["perts"] = [str(p) for p in ref["perts"]]
    return ref
