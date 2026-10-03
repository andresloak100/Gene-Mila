"""Ingest a real single-cell perturbation screen from one or more .h5ad files.

Handles both common layouts:
  * scPerturb (the files CellForge downloads, e.g. AdamsonWeissman2016_*.h5ad):
    obs['perturbation'] with 'control' for controls, raw counts in X.
  * GEARS (perturb_processed.h5ad): obs['condition'] with 'ctrl', 'GENE+ctrl', log-normalised X.

Steps: detect raw counts and normalise them (counts per 10k, log1p, as in
scanpy/cell-eval); parse target genes out of perturbation labels; optionally
merge labels that target the same gene set (several guides per gene); keep
highly variable genes plus every measured target gene; split by perturbation;
keep pseudobulk means of training perturbations (public), and cells of
held-out perturbations plus a control sample (private, for cell-eval).

CellForge downloads (scPerturb RNA archive, https://zenodo.org/records/13350497):
    AdamsonWeissman2016_GSM2406675_10X001.h5ad
    AdamsonWeissman2016_GSM2406677_10X005.h5ad
    AdamsonWeissman2016_GSM2406681_10X010.h5ad
    NormanWeissman2019_filtered.h5ad
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np

from .bundle import make_splits, split_id_for, write_bundle

CONTROL_LABELS = {"control", "ctrl", "non-targeting", "nontargeting", "non_targeting", "nt", "neg", "negative"}


def _looks_like_counts(X) -> bool:
    import scipy.sparse as sp
    data = X.data[:100_000] if sp.issparse(X) else np.asarray(X[:200]).ravel()
    data = data[data != 0]
    return data.size > 0 and bool(np.allclose(data, np.round(data))) and float(data.max()) > 20


def _normalise_log1p(X):
    import scipy.sparse as sp
    X = sp.csr_matrix(X, dtype=np.float32) if sp.issparse(X) else np.asarray(X, dtype=np.float32)
    totals = np.asarray(X.sum(axis=1)).ravel()
    scale = 1e4 / np.where(totals > 0, totals, 1.0)
    if sp.issparse(X):
        X = sp.diags(scale.astype(np.float32)) @ X
        X.data = np.log1p(X.data)
        return X.tocsr()
    return np.log1p(X * scale[:, None])


def parse_targets(label: str, gene_set: set[str]) -> list[str]:
    """Target genes in a perturbation label: tokens split on + _ | , ; that are measured gene names."""
    tokens = [t for t in re.split(r"[+_|,;\s]+", label) if t]
    seen = []
    for t in tokens:
        if t in gene_set and t not in seen:
            seen.append(t)
    return seen


def ingest_h5ad(
    h5ad: Path | list[Path],
    out_dir: Path,
    name: str,
    condition_key: str | None = None,
    control_value: str | None = None,
    gene_name_key: str = "gene_name",
    n_hvg: int = 2000,
    max_control_cells: int = 2000,
    max_eval_cells: int = 300,
    min_cells: int = 20,
    collapse_by_target: bool = True,
    seed: int = 0,
    splits_file: Path | None = None,
) -> Path:
    import anndata as ad
    import scipy.sparse as sp

    paths = [Path(p) for p in (h5ad if isinstance(h5ad, (list, tuple)) else [h5ad])]
    parts = [ad.read_h5ad(p) for p in paths]
    adata = parts[0] if len(parts) == 1 else ad.concat(parts, join="inner", label="source_file",
                                                        keys=[p.name for p in paths], index_unique="-")
    if condition_key is None:
        condition_key = next((k for k in ("perturbation", "condition", "target_gene", "gene", "guide_ids")
                              if k in adata.obs), None)
        if condition_key is None:
            raise ValueError(f"cannot find the perturbation column in obs: {list(adata.obs.columns)}")
    cond = adata.obs[condition_key].astype(str).values
    if control_value is None:
        found = [c for c in np.unique(cond) if c.lower() in CONTROL_LABELS]
        if len(found) != 1:
            raise ValueError(f"cannot identify the control label among {sorted(np.unique(cond))[:20]}; "
                             "pass --control explicitly")
        control_value = found[0]
    genes = (adata.var[gene_name_key] if gene_name_key in adata.var else adata.var_names).astype(str).tolist()
    gene_set = set(genes)

    X = adata.X
    raw_counts = _looks_like_counts(X)
    if raw_counts:
        X = _normalise_log1p(X)
    X = X.tocsr() if sp.issparse(X) else X

    def dense(rows):
        sub = X[rows]
        return np.asarray(sub.todense() if sp.issparse(sub) else sub, dtype=np.float32)

    is_ctrl = cond == control_value
    rng = np.random.default_rng(seed)
    ctrl_idx = np.flatnonzero(is_ctrl)
    if len(ctrl_idx) < 50:
        raise ValueError(f"only {len(ctrl_idx)} control cells labelled {control_value!r}")
    perm = rng.permutation(ctrl_idx)
    ctrl_public = perm[:max_control_cells]
    ctrl_eval = perm[max_control_cells:max_control_cells + max_eval_cells]
    if len(ctrl_eval) < 50:  # not enough controls to keep the two samples disjoint
        ctrl_eval = perm[-max_eval_cells:]

    # group perturbation labels by their measured target-gene set
    groups: dict[str, list[str]] = {}
    targets: dict[str, list[str]] = {}
    dropped = []
    for c in np.unique(cond[~is_ctrl]):
        tg = parse_targets(c, gene_set)
        if not tg:
            dropped.append(c)
            continue
        key = "+".join(tg) if collapse_by_target else c
        groups.setdefault(key, []).append(c)
        targets[key] = tg

    ctrl_dense = dense(ctrl_public)
    var = ctrl_dense.var(axis=0)
    hvg = set(np.argsort(-var)[:n_hvg].tolist())
    hvg |= {i for i, g in enumerate(genes) if g in {t for ts in targets.values() for t in ts}}
    keep = np.array(sorted(hvg))

    pert_means, pert_ncells, rows_by = {}, {}, {}
    for key, labels in groups.items():
        rows = np.flatnonzero(np.isin(cond, labels))
        if len(rows) < min_cells:
            continue
        rows_by[key] = rows
        pert_means[key] = dense(rows)[:, keep].mean(axis=0)
        pert_ncells[key] = len(rows)
    targets = {k: v for k, v in targets.items() if k in pert_means}

    if splits_file:  # an externally defined split (e.g. CellForge's) instead of our seeded one
        ext = json.loads(Path(splits_file).read_text())
        alias = {"val1": ("val1", "val", "valid", "validation"), "val2": ("val2", "test")}
        pick = {"train": "train", **{ours: next((k for k in names if k in ext), None) for ours, names in alias.items()}}
        if None in pick.values():
            raise ValueError(f"splits file needs train/val1/val2 (or train/val/test) lists, has {sorted(ext)}")
        splits = {ours: sorted(p for p in ext[theirs] if p in pert_means) for ours, theirs in pick.items()}
        splits["seed"] = f"external:{Path(splits_file).name}"
        splits["split_id"] = split_id_for(splits)
        in_split = set(splits["train"]) | set(splits["val1"]) | set(splits["val2"])
        pert_means = {k: v for k, v in pert_means.items() if k in in_split}
        targets = {k: v for k, v in targets.items() if k in in_split}
    else:
        splits = make_splits(list(pert_means), seed=seed)

    eval_cells = {"control": dense(ctrl_eval)[:, keep]}
    for key in splits["val1"] + splits["val2"]:
        rows = rows_by[key]
        if len(rows) > max_eval_cells:
            rows = rng.choice(rows, size=max_eval_cells, replace=False)
        eval_cells[key] = dense(np.sort(rows))[:, keep]

    return write_bundle(
        Path(out_dir), name, [genes[i] for i in keep], ctrl_dense[:, keep], pert_means, pert_ncells,
        targets, splits, eval_cells=eval_cells,
        extra_meta={"source": [str(p) for p in paths], "condition_key": condition_key,
                    "control_value": control_value, "raw_counts_normalised": raw_counts, "n_hvg": n_hvg,
                    "collapse_by_target": collapse_by_target, "dropped_labels": dropped[:50],
                    "n_dropped_labels": len(dropped)},
    )


def describe_h5ad(path: Path) -> dict:
    """Quick summary used to choose files and arguments before ingesting."""
    import anndata as ad
    a = ad.read_h5ad(path, backed="r")
    out = {"file": str(path), "n_cells": a.n_obs, "n_genes": a.n_vars, "obs_columns": list(a.obs.columns)}
    for k in ("perturbation", "condition", "target_gene", "gene"):
        if k in a.obs:
            vc = a.obs[k].astype(str).value_counts()
            out.update(condition_key=k, n_labels=int(len(vc)), top_labels=vc.head(8).to_dict(),
                       median_cells_per_label=float(vc.median()))
            break
    return out
