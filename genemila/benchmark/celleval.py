"""Scoring with Arc Institute's cell-eval (https://github.com/ArcInstitute/cell-eval).

Our models predict each perturbation's mean shift from control (delta).
Following cell-eval's own mean baseline (`build_base_mean_adata`), a
prediction becomes (mean of the held-out control cells + predicted delta),
repeated for as many cells as the real perturbed population, and the same
real control cells are attached to both the predicted and the real AnnData.
Anchoring on the held-out controls keeps the public/held-out control sampling
difference out of the delta metrics.
Distribution-level metrics therefore treat the prediction as a point mass;
pseudobulk metrics (pearson_delta, mse, mae, overlap/precision of DE genes,
discrimination scores) are directly comparable with other methods.

Only the controller and the query-only oracle call this module.
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import numpy as np

PERT_COL = "target"
CONTROL = "control"


def available() -> bool:
    try:
        import cell_eval  # noqa: F401
        return True
    except ImportError:
        return False


def load_real_cells(data_dir: Path, part: str):
    import scipy.sparse as sp
    X = sp.load_npz(Path(data_dir) / "private" / f"{part}_cells.npz")
    labels = np.load(Path(data_dir) / "private" / f"{part}_cells_labels.npy", allow_pickle=False)
    return X, labels.astype(str)


def build_pair(pred_delta: dict[str, np.ndarray], X_real, labels: np.ndarray, genes: list[str]):
    import anndata as ad
    import pandas as pd
    import scipy.sparse as sp
    perts = [p for p in dict.fromkeys(labels) if p != CONTROL and p in pred_delta]
    if not perts:
        raise ValueError("no predicted perturbation has held-out cells")
    keep = np.isin(labels, perts + [CONTROL])
    X_real, labels = X_real[keep], labels[keep]
    var = pd.DataFrame(index=pd.Index(genes, name="gene"))
    real = ad.AnnData(X=sp.csr_matrix(X_real, dtype=np.float32),
                      obs=pd.DataFrame({PERT_COL: labels}, index=[f"r{i}" for i in range(len(labels))]), var=var)
    ctrl = X_real[labels == CONTROL]
    ctrl_mean = np.asarray(ctrl.mean(axis=0)).ravel()
    blocks, obs = [], []
    for p in perts:
        n = int((labels == p).sum())
        mean = np.clip(ctrl_mean + np.asarray(pred_delta[p], dtype=np.float64), 0, None).astype(np.float32)
        blocks.append(sp.csr_matrix(np.tile(mean, (n, 1))))
        obs += [p] * n
    blocks.append(sp.csr_matrix(ctrl, dtype=np.float32))
    obs += [CONTROL] * ctrl.shape[0]
    pred = ad.AnnData(X=sp.vstack(blocks).tocsr(),
                      obs=pd.DataFrame({PERT_COL: obs}, index=[f"p{i}" for i in range(len(obs))]), var=var.copy())
    return pred, real


def score(pred_delta: dict[str, np.ndarray], X_real, labels: np.ndarray, genes: list[str],
          profile: str = "full", outdir: Path | None = None, num_threads: int = 1) -> dict:
    """Return cell-eval's mean of each metric over the held-out perturbations.

    pred_delta maps perturbation -> predicted (perturbed mean - control mean) per gene. With outdir,
    cell-eval's per-perturbation and aggregate CSVs are written there."""
    import logging
    import os
    os.environ.setdefault("TQDM_DISABLE", "1")
    from cell_eval import MetricsEvaluator
    logging.getLogger("cell_eval").setLevel(logging.ERROR)
    pred, real = build_pair(pred_delta, X_real, labels, genes)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(outdir) if outdir else Path(tmp)
        ev = MetricsEvaluator(adata_pred=pred, adata_real=real, control_pert=CONTROL, pert_col=PERT_COL,
                              num_threads=num_threads, outdir=str(out))
        results, agg = ev.compute(profile=profile, write_csv=outdir is not None)
    agg = agg.to_pandas()
    stat_col = agg.columns[0]
    row = agg[agg[stat_col] == "mean"].iloc[0]
    return {k: (None if row[k] is None or (isinstance(row[k], float) and np.isnan(row[k])) else float(row[k]))
            for k in agg.columns[1:]}
