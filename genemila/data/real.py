"""Ingest a real single-cell perturbation screen from an .h5ad file.

Supports the GEARS-style layout used by the CellForge datasets (Adamson,
Norman): obs['condition'] values like 'ctrl', 'GENE+ctrl', 'GENEA+GENEB', and
var['gene_name']. Only pseudobulk means of perturbed populations and a
subsample of control cells are kept, so the bundle stays small.

Download for Adamson (GEARS preprocessing, ~70 MB):
    https://dataverse.harvard.edu/api/access/datafile/6154417  (tar.gz with adamson/perturb_processed.h5ad)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .bundle import make_splits, write_bundle


def ingest_h5ad(
    h5ad: Path,
    out_dir: Path,
    name: str,
    condition_key: str = "condition",
    control_value: str = "ctrl",
    gene_name_key: str = "gene_name",
    n_hvg: int = 2000,
    max_control_cells: int = 2000,
    min_cells: int = 20,
    seed: int = 0,
) -> Path:
    import anndata as ad
    import scipy.sparse as sp

    adata = ad.read_h5ad(h5ad)
    genes = (adata.var[gene_name_key] if gene_name_key in adata.var else adata.var_names).astype(str).tolist()
    X = adata.X
    cond = adata.obs[condition_key].astype(str).values
    is_ctrl = cond == control_value

    def dense(rows):
        sub = X[rows]
        return np.asarray(sub.todense() if sp.issparse(sub) else sub, dtype=np.float32)

    ctrl_idx = np.flatnonzero(is_ctrl)
    rng = np.random.default_rng(seed)
    ctrl_sample = rng.choice(ctrl_idx, size=min(len(ctrl_idx), max_control_cells), replace=False)
    ctrl = dense(ctrl_sample)

    # Highly variable genes chosen on control cells plus every perturbed target gene.
    targets = {}
    for c in np.unique(cond[~is_ctrl]):
        targets[c] = [g for g in c.split("+") if g != control_value]
    target_genes = {g for ts in targets.values() for g in ts}
    var = ctrl.var(axis=0)
    hvg = set(np.argsort(-var)[:n_hvg].tolist())
    hvg |= {i for i, g in enumerate(genes) if g in target_genes}
    keep = np.array(sorted(hvg))

    pert_means, pert_ncells = {}, {}
    for c in targets:
        rows = np.flatnonzero(cond == c)
        if len(rows) < min_cells:
            continue
        pert_means[c] = dense(rows)[:, keep].mean(axis=0)
        pert_ncells[c] = len(rows)
    targets = {c: ts for c, ts in targets.items() if c in pert_means}
    splits = make_splits(list(pert_means), seed=seed)
    return write_bundle(
        Path(out_dir), name, [genes[i] for i in keep], ctrl[:, keep], pert_means, pert_ncells,
        targets, splits, extra_meta={"source": str(h5ad), "n_hvg": n_hvg},
    )
