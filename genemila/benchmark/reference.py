"""Ground-truth differential-expression reference for held-out perturbations.

Built from the private held-out cells (perturbed cells vs. the held-out control
sample) once per dataset, and used by the comparable metrics:

* top-20 DE genes per perturbation (CellForge's "_DE" metrics, paper Table 1):
  ranked by |z| of the Wilcoxon rank-sum test against control, the test
  CellForge's docs name (docs/RESULTS.md); optionally excluding genes that are
  zero in every perturbed cell ("non-dropout", as GEARS does).
* CellForge's documented DE set: Wilcoxon, Benjamini-Hochberg adjusted
  p < 0.05 and |log2 fold change| > 0.5.
* DE labels and directions per (perturbation, gene), as in VCWorld: Wilcoxon,
  BH-adjusted p <= 0.05 and |log2FC| >= 0.25.
Fold changes use scanpy's definition for log1p data. CellForge's repository
has no evaluation code, so its definitions are reconstructed from its paper and
docs; see docs/ARCHITECTURE.md.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

DE_PADJ = 0.05
DE_LOGFC = 0.25           # VCWorld
CELLFORGE_DE_LOGFC = 0.5  # CellForge docs
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


def build(X, labels: np.ndarray, top_k: int = TOP_K, non_dropout: bool = False) -> dict:
    """X: cells x genes (log-normalised), labels: 'control' or the perturbation per cell."""
    from scipy.stats import mannwhitneyu
    import scipy.sparse as sp
    X = X.toarray() if sp.issparse(X) else np.asarray(X)
    X = X.astype(np.float64)
    ctrl = X[labels == "control"]
    perts = [p for p in dict.fromkeys(labels.tolist()) if p != "control"]
    top, de, de_cf, direction, logfc, padj = [], [], [], [], [], []
    n2 = ctrl.shape[0]
    for p in perts:
        cells = X[labels == p]
        n1 = cells.shape[0]
        lfc = log2_fc(cells.mean(0), ctrl.mean(0))
        varies = (cells.max(0) > cells.min(0)) | (ctrl.max(0) > ctrl.min(0)) | (cells.max(0) != ctrl.max(0))
        pv, z = np.ones(X.shape[1]), np.zeros(X.shape[1])
        if varies.any():
            res = mannwhitneyu(cells[:, varies], ctrl[:, varies], axis=0, alternative="two-sided")
            pv[varies] = res.pvalue
            z[varies] = (res.statistic - n1 * n2 / 2) / np.sqrt(n1 * n2 * (n1 + n2 + 1) / 12)
        pa = _bh(np.nan_to_num(pv, nan=1.0))
        score = np.abs(z) + 1e-6 * np.abs(lfc)  # |z| ranks as p does without underflow; |log2FC| breaks ties
        if non_dropout:
            score = np.where((cells != 0).any(0), score, -1.0)
        top.append(np.argsort(-score, kind="stable")[:top_k])
        de.append((pa <= DE_PADJ) & (np.abs(lfc) >= DE_LOGFC))
        de_cf.append((pa < DE_PADJ) & (np.abs(lfc) > CELLFORGE_DE_LOGFC))
        direction.append(np.sign(lfc).astype(np.int8))
        logfc.append(lfc)
        padj.append(pa)
    return {"perts": np.array(perts), "top_de": np.array(top, dtype=np.int64), "de": np.array(de),
            "de_cellforge": np.array(de_cf), "direction": np.array(direction),
            "logfc": np.array(logfc, dtype=np.float32), "padj": np.array(padj, dtype=np.float32),
            "control_mean": ctrl.mean(0), "top_k": top_k, "non_dropout": non_dropout}


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
