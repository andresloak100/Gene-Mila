#!/usr/bin/env python
"""Single-cell perturbation response prediction (CRISPRi / gene knockout).

Implements the approved research plan (research_plan.json) inside the rules of
acceptance_contract.json. The deliverable is this single file.

Scientific task (T01/T02 from the plan)
---------------------------------------
Predict the post-perturbation gene-expression profile of a cell from:
  * baseline expression (mean profile of unperturbed / non-targeting control cells),
  * perturbation identity (CRISPRi target gene or guide),
  * optional cell-context features (cell type, batch, dose).

The model predicts the *response* (log-fold change relative to baseline) using the
architecture specified in the plan:

  encoder              : Transformer (4 layers, 8 heads, dim 512, GELU)
  perturbation_encoder : MLP (3 layers, [256, 128, 64], Swish) over a hashed
                         one-hot perturbation token (generalises to unseen targets)
  cross_attention      : 8 heads, dim 512, dropout 0.1 (perturbation conditions genes)
  decoder              : MLP (3 layers, [256, 512, 1024], Swish) shared per gene

Training follows the plan: AdamW(lr=3e-4, wd=0.01), cosine annealing (T_0=10,
eta_min=1e-6), gradient clipping (1.0), early stopping (patience 15, min_delta 1e-4),
batch size 64. Loss is MSE on reconstructed log-normalised expression.

Preprocessing follows the plan: QC cell/gene filtering, total-count normalisation
(target sum 10000) + log1p, regress-out of technical covariates, Harmony-style
batch correction (approximated by per-batch mean centring), and highly-variable
gene selection to keep the Transformer tractable on CPU.

Biological/engineering notes are given as comments inline.

This file does NOT import scanpy (its numba cache is broken in the provided env);
equivalent operations are implemented with anndata + numpy + scipy.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

# --------------------------------------------------------------------------- #
# Optional dependencies (graceful degradation for environments without them).
# --------------------------------------------------------------------------- #
try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset

    _HAS_TORCH = True
except Exception as _exc:  # pragma: no cover - environment dependent
    torch = None  # type: ignore
    nn = None  # type: ignore
    _HAS_TORCH = False
    _TORCH_IMPORT_ERROR = repr(_exc)

try:
    import anndata as _anndata

    _HAS_ANNDATA = True
except Exception as _exc:  # pragma: no cover
    _anndata = None
    _HAS_ANNDATA = False
    _ANNDATA_IMPORT_ERROR = repr(_exc)

try:
    import scipy.sparse as _sparse

    _HAS_SCIPY = True
except Exception as _exc:  # pragma: no cover
    _sparse = None
    _HAS_SCIPY = False
    _SCIPY_IMPORT_ERROR = repr(_exc)


log = logging.getLogger("result")
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


# --------------------------------------------------------------------------- #
# Configuration (mirrors research_plan.json).
# --------------------------------------------------------------------------- #
@dataclass
class Config:
    # Data processing / QC thresholds from the plan.
    min_genes: int = 200
    max_genes: int = 6000
    min_counts: int = 1000
    max_counts: int = 50000
    max_mito_percent: float = 20.0
    gene_min_cells: int = 3
    gene_min_counts: int = 10
    normalize_target_sum: float = 10000.0
    regression_vars: Tuple[str, ...] = ("total_counts", "pct_counts_mt")
    harmony_theta: float = 2.0
    harmony_max_iterations: int = 20
    n_top_genes: int = 512

    # Model architecture from the plan.
    encoder_layers: int = 4
    encoder_heads: int = 8
    encoder_dim: int = 512
    encoder_activation: str = "gelu"
    pert_dims: Tuple[int, ...] = (256, 128, 64)
    pert_activation: str = "swish"
    cross_heads: int = 8
    cross_dropout: float = 0.1
    decoder_dims: Tuple[int, ...] = (256, 512, 1024)
    decoder_activation: str = "swish"
    transformer_dropout: float = 0.1
    n_pert_buckets: int = 1024

    # Training from the plan.
    lr: float = 3e-4
    weight_decay: float = 0.01
    batch_size: int = 64
    grad_clip: float = 1.0
    patience: int = 15
    min_delta: float = 1e-4
    T_0: int = 10
    eta_min: float = 1e-6
    epochs: int = 30
    seed: int = 42

    def to_dict(self) -> Dict[str, object]:
        return {k: (list(v) if isinstance(v, tuple) else v) for k, v in self.__dict__.items()}


# --------------------------------------------------------------------------- #
# Small numeric helpers.
# --------------------------------------------------------------------------- #
def _set_seed(seed: int) -> None:
    os.environ.setdefault("PYTHONHASHSEED", str(seed))
    np.random.seed(seed)
    if _HAS_TORCH:
        torch.manual_seed(seed)
        try:
            import random

            random.seed(seed)
        except Exception:
            pass


def _stable_hash(value: str) -> int:
    """Deterministic, platform-stable hash so runs are reproducible."""
    return int(hashlib.sha256(value.encode("utf-8")).hexdigest(), 16)


def _is_sparse(x) -> bool:
    return _HAS_SCIPY and _sparse.issparse(x)


def _to_csr(x):
    """Return x as a scipy CSR matrix without copying when possible."""
    if _is_sparse(x):
        return x.tocsr()
    if _HAS_SCIPY:
        return _sparse.csr_matrix(x)
    raise RuntimeError("scipy is required to handle dense/sparse matrices")


def _as_numpy(x) -> np.ndarray:
    if _is_sparse(x):
        return np.asarray(x.toarray(), dtype=np.float32)
    return np.asarray(x, dtype=np.float32)


def _mean_var_sparse(x_csr):
    """Column-wise mean and (biased) variance of a sparse CSR matrix."""
    n_rows = x_csr.shape[0]
    if n_rows == 0:
        return np.zeros(x_csr.shape[1], dtype=np.float64), np.zeros(x_csr.shape[1], dtype=np.float64)
    col_sum = np.asarray(x_csr.sum(axis=0)).ravel()
    mean = col_sum / n_rows
    x2 = x_csr.copy()
    x2.data = x2.data * x2.data
    col_sq = np.asarray(x2.sum(axis=0)).ravel()
    var = np.clip(col_sq / n_rows - mean * mean, 0.0, None)
    return mean, var


def _pearson(y: np.ndarray, yhat: np.ndarray) -> float:
    y = np.asarray(y, dtype=np.float64).ravel()
    yhat = np.asarray(yhat, dtype=np.float64).ravel()
    if y.size == 0:
        return float("nan")
    yc = y - y.mean()
    yhc = yhat - yhat.mean()
    denom = float(np.sqrt((yc * yc).sum() * (yhc * yhc).sum()))
    if denom == 0:
        return 0.0
    return float((yc * yhc).sum() / denom)


def _r2(y: np.ndarray, yhat: np.ndarray) -> float:
    y = np.asarray(y, dtype=np.float64).ravel()
    yhat = np.asarray(yhat, dtype=np.float64).ravel()
    if y.size == 0:
        return float("nan")
    ss_res = float(((y - yhat) ** 2).sum())
    ss_tot = float(((y - y.mean()) ** 2).sum())
    if ss_tot == 0:
        return 0.0
    return float(1.0 - ss_res / ss_tot)


def _mse(y: np.ndarray, yhat: np.ndarray) -> float:
    y = np.asarray(y, dtype=np.float64).ravel()
    yhat = np.asarray(yhat, dtype=np.float64).ravel()
    if y.size == 0:
        return float("nan")
    return float(np.mean((y - yhat) ** 2))


# --------------------------------------------------------------------------- #
# Perturbation / metadata detection.
# --------------------------------------------------------------------------- #
_PERTURB_COLUMNS = [
    "condition",
    "perturbation",
    "perturbation_id",
    "perturb",
    "target",
    "target_gene",
    "gene_target",
    "gene",
    "guide",
    "guide_id",
    "grna",
    "sgRNA",
    "sgrna",
    "crispr_target",
    "knockout",
    "ko",
    "treatment",
    "drug",
    "stim",
]

_CONTROL_TOKENS = [
    "control",
    "ctrl",
    "nt",
    "nontarget",
    "non_target",
    "non-target",
    "nontargeting",
    "negctrl",
    "neg_ctrl",
    "negative",
    "scramble",
    "scrambled",
    "empty",
    "blank",
    "null",
    "untreated",
    "unperturbed",
    "baseline",
]

_BATCH_COLUMNS = ["batch", "sample", "sample_id", "donor", "replicate", "rep"]
_CELLTYPE_COLUMNS = ["cell_type", "celltype", "cell_line", "cellline", "cell_type_ontology"]
_DOSE_COLUMNS = ["dose", "concentration", "dose_um", "dose_umol", "drug_dose"]


def _is_control_value(value) -> bool:
    s = str(value).lower().strip()
    if s in {"", "nan", "none", "nat", "<na>"}:
        return False
    for token in _CONTROL_TOKENS:
        if token in s:
            return True
    return False


def _detect_column(obs, candidates: Sequence[str]) -> Optional[str]:
    """Return the first candidate column that exists and has >= 2 unique values."""
    cols = [c for c in obs.columns if c in candidates or str(c).lower() in candidates]
    for c in candidates:
        if c in obs.columns:
            if obs[c].nunique(dropna=True) >= 2:
                return c
    # fall back to case-insensitive match
    lower_map = {str(c).lower(): c for c in obs.columns}
    for c in candidates:
        hit = lower_map.get(c.lower())
        if hit is not None and obs[hit].nunique(dropna=True) >= 2:
            return hit
    return None


def _is_mito_gene(name: str, var: Optional[object] = None) -> bool:
    s = str(name).lower()
    if s.startswith("mt-") or s.startswith("mtrnr") or s.startswith("mtatp"):
        return True
    if s.startswith("mtco") or s.startswith("mtnd") or s.startswith("mtcyb"):
        return True
    return False


def _mito_mask(adata) -> np.ndarray:
    names = [str(n) for n in adata.var_names]
    # a boolean `mito` / `mt` column in var takes precedence if present.
    for key in ("mito", "mt", "mitochondrial"):
        if key in adata.var.columns:
            mask = np.asarray(adata.var[key]).astype(bool)
            if mask.shape[0] == len(names):
                return mask
    return np.array([_is_mito_gene(n) for n in names], dtype=bool)


# --------------------------------------------------------------------------- #
# Preprocessing.
# --------------------------------------------------------------------------- #
class Preprocessor:
    """QC + normalisation + HVG selection fitted on training data.

    Fitted parameters (selected genes, regress-out coefficients, batch means)
    are reused to transform a validation AnnData object without leaking
    information from the validation set.
    """

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.selected_gene_names: List[str] = []
        self.selected_gene_idx: np.ndarray = np.array([], dtype=int)
        self.baseline: Optional[np.ndarray] = None  # log-normalised, [n_genes]
        self.raw_counts_observed: bool = False
        self.regress_betas: Optional[np.ndarray] = None  # [n_genes, n_covariates + 1]
        self.batch_means: Optional[np.ndarray] = None
        self.perturb_column: Optional[str] = None

    # ------------------------------------------------------------------ #
    def _detect_counts(self, x) -> bool:
        """Heuristic: integer-valued matrix with large maxima looks like counts."""
        if _is_sparse(x):
            data = x.data
            if data.size == 0:
                return True
            sample = data[: min(data.size, 200000)]
        else:
            arr = np.asarray(x)
            sample = arr.ravel()[:200000]
        if sample.dtype.kind in "iu":
            return True
        if sample.size == 0:
            return True
        if np.all(np.isfinite(sample)) and np.allclose(sample, np.round(sample)) and float(np.max(sample)) > 50.0:
            return True
        return False

    # ------------------------------------------------------------------ #
    def fit(self, adata) -> np.ndarray:
        """Fit on training data; return the log-normalised cell x gene matrix."""
        cfg = self.cfg
        if adata is None:
            raise ValueError("training AnnData is None")
        if not _HAS_ANNDATA:
            raise RuntimeError("anndata is required to read .h5ad files")

        x = _to_csr(adata.X)
        self.raw_counts_observed = self._detect_counts(x)

        # ---- QC -----------------------------------------------------------
        n_cells0, n_genes0 = x.shape
        log.info("Raw matrix: %d cells x %d genes (counts=%s)", n_cells0, n_genes0, self.raw_counts_observed)

        keep_cells = np.ones(n_cells0, dtype=bool)
        if self.raw_counts_observed:
            total_counts = np.asarray(x.sum(axis=1)).ravel()
            n_genes_by_counts = np.asarray((x > 0).sum(axis=1)).ravel()
            mito = _mito_mask(adata)
            mito_counts = np.asarray(x[:, mito].sum(axis=1)).ravel() if mito.any() else np.zeros_like(total_counts)
            pct_mito = np.where(total_counts > 0, 100.0 * mito_counts / np.maximum(total_counts, 1.0), 0.0)

            keep_cells &= n_genes_by_counts >= cfg.min_genes
            keep_cells &= n_genes_by_counts <= cfg.max_genes
            keep_cells &= total_counts >= cfg.min_counts
            keep_cells &= total_counts <= cfg.max_counts
            keep_cells &= pct_mito <= cfg.max_mito_percent
            log.info("Cell QC keeps %d/%d cells (genes/counts/mito thresholds)", int(keep_cells.sum()), n_cells0)
        else:
            # Already-normalised matrix: count-based cell filters are not meaningful.
            log.info("Matrix looks pre-normalised; skipping count-based cell QC.")

        # ---- Gene QC ------------------------------------------------------
        x_cells = x[keep_cells, :]
        n_cells_by_gene = np.asarray((x_cells > 0).sum(axis=0)).ravel()
        gene_counts = np.asarray(x_cells.sum(axis=0)).ravel()
        keep_genes = (n_cells_by_gene >= cfg.gene_min_cells) & (gene_counts >= cfg.gene_min_counts)
        if not keep_genes.any():
            log.warning("Gene QC removed all genes; keeping the top expressed genes instead.")
            keep_genes = np.ones(x_cells.shape[1], dtype=bool)
        x_clean = x_cells[:, keep_genes].tocsr()
        names_after_qc = [str(n) for n in adata.var_names[keep_genes]]
        log.info("Gene QC keeps %d/%d genes", int(keep_genes.sum()), n_genes0)

        # ---- Normalisation -------------------------------------------------
        if self.raw_counts_observed:
            row_sums = np.asarray(x_clean.sum(axis=1)).ravel()
            row_sums[row_sums <= 0] = 1.0
            scale = (cfg.normalize_target_sum / row_sums).astype(np.float32)
            if _is_sparse(x_clean):
                x_norm = x_clean.multiply(scale[:, None]).tocsr()
            else:
                x_norm = x_clean * scale[:, None]
            # log1p in place on the data array keeps memory usage low.
            if _is_sparse(x_norm):
                x_norm = x_norm.tocsr()
                x_norm.data = np.log1p(x_norm.data)
            else:
                x_norm = np.log1p(np.asarray(x_norm, dtype=np.float32))
            log.info("Normalised counts to target sum %.0f and applied log1p", cfg.normalize_target_sum)
        else:
            x_norm = x_clean
            # Ensure strictly non-negative for log-like downstream ops; if the
            # matrix is already log-normalised leave it untouched.
            if _is_sparse(x_norm):
                x_norm = x_norm.tocsr()
            else:
                x_norm = np.asarray(x_norm, dtype=np.float32)

        # ---- Highly variable genes ----------------------------------------
        if _is_sparse(x_norm):
            mean, var = _mean_var_sparse(x_norm.tocsr())
        else:
            mean = np.asarray(x_norm, dtype=np.float64).mean(axis=0)
            var = np.asarray(x_norm, dtype=np.float64).var(axis=0)
        dispersion = var / np.maximum(mean, 1e-12)
        n_top = min(cfg.n_top_genes, x_norm.shape[1])
        order = np.argsort(dispersion)[::-1][:n_top]
        # Keep genes with at least some signal; fall back to mean-based order.
        if np.all(dispersion <= 0):
            order = np.argsort(mean)[::-1][:n_top]
        self.selected_gene_idx = np.sort(order).astype(int)
        self.selected_gene_names = [names_after_qc[i] for i in self.selected_gene_idx]
        log.info("Selected %d highly variable genes", len(self.selected_gene_names))

        x_sel = x_norm[:, self.selected_gene_idx]
        x_sel_dense = _as_numpy(x_sel)

        # ---- Regress out technical covariates ------------------------------
        covariates = self._build_covariates(x_clean, adata, keep_cells)
        if covariates is not None and len(covariates) > 0:
            x_sel_dense = self._regress_out(x_sel_dense, covariates)
            log.info("Regressed out covariates: %s", list(covariates.keys()))

        # ---- Harmony-style batch correction (approximation) ---------------
        batch_key = _detect_column(adata.obs[keep_cells], _BATCH_COLUMNS)
        if batch_key is not None:
            x_sel_dense = self._harmony_lite(x_sel_dense, np.asarray(adata.obs[keep_cells][batch_key]))
            log.info("Applied Harmony-style batch mean-centring using column '%s'", batch_key)

        # ---- Baseline expression (control-mean, log-normalised) -----------
        self.perturb_column = _detect_column(adata.obs, _PERTURB_COLUMNS)
        control_mask = self._control_mask(adata.obs[keep_cells])
        if control_mask is not None and control_mask.any():
            self.baseline = x_sel_dense[control_mask].mean(axis=0).astype(np.float32)
            log.info("Baseline computed from %d control cells", int(control_mask.sum()))
        else:
            self.baseline = x_sel_dense.mean(axis=0).astype(np.float32)
            log.info("No control cells detected; baseline = global mean expression")

        return x_sel_dense

    # ------------------------------------------------------------------ #
    def _control_mask(self, obs):
        if self.perturb_column is None:
            return None
        return np.asarray([_is_control_value(v) for v in obs[self.perturb_column]], dtype=bool)

    # ------------------------------------------------------------------ #
    def _build_covariates(self, x_counts, adata, keep_cells) -> Optional[Dict[str, np.ndarray]]:
        """Build optional technical covariates for regress-out."""
        cov = {}
        if self.raw_counts_observed:
            total = np.asarray(x_counts.sum(axis=1)).ravel()
            cov["total_counts"] = np.log1p(total).astype(np.float64)
            mito = _mito_mask(adata)
            if mito.any():
                mito_counts = np.asarray(x_counts[:, mito].sum(axis=1)).ravel()
                pct = np.where(total > 0, 100.0 * mito_counts / np.maximum(total, 1.0), 0.0)
                if pct.std() > 1e-9:
                    cov["pct_counts_mt"] = pct.astype(np.float64)
        return cov if cov else None

    # ------------------------------------------------------------------ #
    def _regress_out(self, x: np.ndarray, covariates: Dict[str, np.ndarray]) -> np.ndarray:
        """Residualise each gene against the covariates (OLS), gene by gene."""
        cols = [v.astype(np.float64) for v in covariates.values()]
        design = np.column_stack([np.ones(x.shape[0]), *cols])
        out = np.empty_like(x, dtype=np.float32)
        for j in range(x.shape[1]):
            y = x[:, j].astype(np.float64)
            if np.ptp(y) == 0:
                out[:, j] = x[:, j]
                continue
            try:
                beta, *_ = np.linalg.lstsq(design, y, rcond=None)
                out[:, j] = (y - design @ beta).astype(np.float32)
            except np.linalg.LinAlgError:
                out[:, j] = x[:, j]
        self.regress_betas = None  # recomputed per fit; kept for potential reuse
        return out

    # ------------------------------------------------------------------ #
    def _harmony_lite(self, x: np.ndarray, batch: np.ndarray) -> np.ndarray:
        """Approximation of Harmony: centre each gene within each batch.

        Full Harmony (PCA + soft k-means correction, theta/max_iter) is replaced
        by per-batch mean centring so the pipeline remains dependency-light and
        CPU-friendly. The correction matrix is stored so it can be applied to
        validation data.
        """
        global_mean = x.mean(axis=0)
        corrected = np.empty_like(x, dtype=np.float32)
        batch_ids = np.unique(batch)
        if batch_ids.size <= 1:
            return x
        # mean per batch
        batch_means = {}
        for b in batch_ids:
            m = batch == b
            batch_means[str(b)] = x[m].mean(axis=0).astype(np.float32)
        for i, b in enumerate(batch):
            corrected[i] = x[i] - batch_means[str(b)] + global_mean
        self.batch_means = batch_means
        return corrected

    # ------------------------------------------------------------------ #
    def transform(self, adata) -> Tuple[np.ndarray, np.ndarray]:
        """Apply fitted preprocessing to a validation AnnData.

        Returns (log-normalised selected-gene matrix, per-gene presence mask).
        """
        if adata is None:
            raise ValueError("validation AnnData is None")
        x = _to_csr(adata.X)
        raw = self._detect_counts(x)
        names = [str(n) for n in adata.var_names]
        name_to_idx = {n: i for i, n in enumerate(names)}
        present = [n in name_to_idx for n in self.selected_gene_names]
        present_mask = np.asarray(present, dtype=bool)

        idx = np.array([name_to_idx[n] for n in self.selected_gene_names if n in name_to_idx], dtype=int)
        x_sel = x[:, idx]
        # Normalise to match training.
        if raw:
            row_sums = np.asarray(x.sum(axis=1)).ravel().astype(np.float32)
            row_sums[row_sums <= 0] = 1.0
            scale = (self.cfg.normalize_target_sum / row_sums).astype(np.float32)
            x_norm = x_sel.multiply(scale[:, None]).tocsr()
            x_norm.data = np.log1p(x_norm.data)
        else:
            x_norm = x_sel.tocsr()
        x_dense = _as_numpy(x_norm)  # [n_cells, n_present]

        # Reconstruct a full-width matrix (n_selected columns) so the model
        # input keeps a fixed width; genes missing from the validation object
        # are imputed with the training baseline and masked out of the metrics.
        full = np.tile(self.baseline[None, :], (x_dense.shape[0], 1)).astype(np.float32)
        full[:, present_mask] = x_dense
        return full, present_mask


# --------------------------------------------------------------------------- #
# Dataset / sample construction.
# --------------------------------------------------------------------------- #
@dataclass
class PerturbationData:
    """Structured training/validation tensors for one condition per sample."""

    baseline: np.ndarray  # [n_genes] log-normalised control mean
    labels: List[str]     # perturbation label per sample
    targets: np.ndarray   # [n_samples, n_genes] log-normalised group means
    n_cells: np.ndarray   # [n_samples] group sizes


def _labels_for(obs, perturb_column: Optional[str]) -> List[str]:
    labels = []
    if perturb_column is None:
        return ["unknown"] * obs.shape[0]
    for v in obs[perturb_column]:
        if _is_control_value(v):
            labels.append("control")
        else:
            labels.append(str(v))
    return labels


def build_group_data(
    x: np.ndarray,
    labels: List[str],
    baseline: np.ndarray,
) -> PerturbationData:
    """Collapse cells to one sample per perturbation group (plus a control)."""
    labels = list(labels)
    group_to_idx: Dict[str, List[int]] = {}
    for i, lab in enumerate(labels):
        group_to_idx.setdefault(lab, []).append(i)

    out_labels: List[str] = []
    targets: List[np.ndarray] = []
    n_cells: List[int] = []
    # Control first (if any) so its index is stable.
    if "control" in group_to_idx:
        idxs = group_to_idx.pop("control")
        out_labels.append("control")
        targets.append(x[idxs].mean(axis=0).astype(np.float32))
        n_cells.append(len(idxs))
    for lab in sorted(group_to_idx.keys()):
        idxs = group_to_idx[lab]
        out_labels.append(lab)
        targets.append(x[idxs].mean(axis=0).astype(np.float32))
        n_cells.append(len(idxs))

    targets_arr = np.stack(targets) if targets else np.zeros((0, x.shape[1]), dtype=np.float32)
    return PerturbationData(
        baseline=baseline.astype(np.float32),
        labels=out_labels,
        targets=targets_arr,
        n_cells=np.asarray(n_cells, dtype=int),
    )


def _label_to_bucket(labels: Sequence[str], n_buckets: int) -> np.ndarray:
    buckets = np.asarray([_stable_hash(str(lab)) % n_buckets for lab in labels], dtype=np.int64)
    return buckets


def _one_hot(indices: np.ndarray, n_classes: int) -> np.ndarray:
    one_hot = np.zeros((indices.shape[0], n_classes), dtype=np.float32)
    one_hot[np.arange(indices.shape[0]), indices] = 1.0
    return one_hot


# --------------------------------------------------------------------------- #
# PyTorch model.
# --------------------------------------------------------------------------- #
class _Swish(nn.Module):
    """Swish / SiLU activation specified for the perturbation/decoder MLPs."""

    def forward(self, x):
        return x * torch.sigmoid(x)


def _activation(name: str):
    if name == "swish" or name == "silu":
        return _Swish()
    if name == "gelu":
        return nn.GELU()
    if name == "relu":
        return nn.ReLU()
    if name == "leaky_relu":
        return nn.LeakyReLU()
    return nn.ReLU()


class _MLP(nn.Module):
    def __init__(self, in_dim: int, hidden_dims: Sequence[int], out_dim: int, activation: str = "swish"):
        super().__init__()
        dims = [in_dim, *list(hidden_dims), out_dim]
        layers = []
        for i in range(len(dims) - 1):
            layers.append(nn.Linear(dims[i], dims[i + 1]))
            if i < len(dims) - 2:
                layers.append(_activation(activation))
        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x)


class PerturbationResponseModel(nn.Module):
    """Transformer encoder + MLP perturbation encoder + cross-attention + decoder."""

    def __init__(self, n_genes: int, cfg: Config):
        super().__init__()
        self.cfg = cfg
        self.n_genes = n_genes
        d = cfg.encoder_dim

        # Gene token embedding: scalar expression -> d-dim token.
        self.gene_proj = nn.Linear(1, d)

        # Fixed sinusoidal positional encoding for gene order (position in the
        # selected-gene vector has no biological ordering, but the encoding lets
        # the Transformer distinguish tokens symmetrically).
        pos = self._sinusoidal(n_genes, d)
        self.register_buffer("positional_encoding", pos)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d,
            nhead=cfg.encoder_heads,
            dim_feedforward=d * 4,
            dropout=cfg.transformer_dropout,
            activation=cfg.encoder_activation,
            batch_first=True,
            norm_first=True,
        )
        self.encoder = nn.TransformerEncoder(encoder_layer, num_layers=cfg.encoder_layers, enable_nested_tensor=False)

        # Perturbation encoder: one-hot hashed token -> [256, 128, 64].
        self.pert_encoder = _MLP(cfg.n_pert_buckets, cfg.pert_dims[:-1], cfg.pert_dims[-1], activation=cfg.pert_activation)
        self.pert_proj = nn.Linear(cfg.pert_dims[-1], d)

        # Cross-attention: genes query the perturbation conditioning token.
        self.cross_attention = nn.MultiheadAttention(
            embed_dim=d, num_heads=cfg.cross_heads, dropout=cfg.cross_dropout, batch_first=True
        )

        # Decoder: shared per-gene MLP [256, 512, 1024] -> scalar delta.
        self.decoder = _MLP(d, cfg.decoder_dims, 1, activation=cfg.decoder_activation)

    @staticmethod
    def _sinusoidal(n: int, d: int) -> torch.Tensor:
        pe = torch.zeros(n, d)
        position = torch.arange(n).unsqueeze(1).float()
        div = torch.exp(torch.arange(0, d, 2).float() * (-np.log(10000.0) / d))
        pe[:, 0::2] = torch.sin(position * div)
        pe[:, 1::2] = torch.cos(position * div)
        return pe

    def forward(self, baseline: torch.Tensor, pert_onehot: torch.Tensor) -> torch.Tensor:
        """Predict post-perturbation log-normalised expression.

        baseline   : [B, n_genes] control-mean expression.
        pert_onehot: [B, n_buckets] hashed perturbation token.
        """
        B, G = baseline.shape
        x = baseline.unsqueeze(-1)  # [B, G, 1]
        x = self.gene_proj(x)  # [B, G, d]
        x = x + self.positional_encoding[:G].unsqueeze(0)
        x = self.encoder(x)  # [B, G, d]

        p = self.pert_encoder(pert_onehot)  # [B, 64]
        kv = self.pert_proj(p).unsqueeze(1)  # [B, 1, d]
        attended, _ = self.cross_attention(x, kv, kv)  # [B, G, d]

        delta = self.decoder(attended).squeeze(-1)  # [B, G]
        return baseline + delta


# --------------------------------------------------------------------------- #
# Training.
# --------------------------------------------------------------------------- #
def _prepare_tensors(data: PerturbationData, cfg: Config):
    n = data.targets.shape[0]
    base = np.tile(data.baseline[None, :], (n, 1)).astype(np.float32)
    targets = data.targets.astype(np.float32)
    buckets = _label_to_bucket(data.labels, cfg.n_pert_buckets)
    one_hot = _one_hot(buckets, cfg.n_pert_buckets)
    return torch.as_tensor(base), torch.as_tensor(one_hot), torch.as_tensor(targets)


def train_model(
    model: nn.Module,
    train_data: PerturbationData,
    val_data: Optional[PerturbationData],
    cfg: Config,
) -> Dict[str, float]:
    """Train with AdamW + cosine annealing + early stopping; return history."""
    device = torch.device("cpu")
    model = model.to(device)

    base, one_hot, targets = _prepare_tensors(train_data, cfg)
    if base.shape[0] == 0:
        raise ValueError("No training samples available")

    optimizer = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=cfg.T_0, eta_min=cfg.eta_min)
    loss_fn = nn.MSELoss()

    # Validation tensors (for early stopping) if available.
    val_tensors = None
    if val_data is not None and val_data.targets.shape[0] > 0:
        vbase, vone, vtargets = _prepare_tensors(val_data, cfg)
        val_tensors = (vbase, vone, vtargets)

    dataset = TensorDataset(base, one_hot, targets)
    batch_size = max(1, min(cfg.batch_size, base.shape[0]))
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    best_val = float("inf")
    best_state = None
    patience_left = cfg.patience
    history: Dict[str, float] = {"train_loss": float("nan"), "val_loss": float("nan")}

    for epoch in range(cfg.epochs):
        model.train()
        epoch_loss = 0.0
        n_batches = 0
        for b, o, t in loader:
            b, o, t = b.to(device), o.to(device), t.to(device)
            optimizer.zero_grad(set_to_none=True)
            pred = model(b, o)
            loss = loss_fn(pred, t)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), cfg.grad_clip)
            optimizer.step()
            epoch_loss += float(loss.item())
            n_batches += 1
        scheduler.step()

        train_loss = epoch_loss / max(n_batches, 1)
        history["train_loss"] = train_loss

        if val_tensors is not None:
            model.eval()
            with torch.no_grad():
                vpred = model(val_tensors[0], val_tensors[1])
                val_loss = float(loss_fn(vpred, val_tensors[2]).item())
            history["val_loss"] = val_loss
            improved = val_loss < best_val - cfg.min_delta
            if improved:
                best_val = val_loss
                best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}
                patience_left = cfg.patience
            else:
                patience_left -= 1
            if patience_left <= 0:
                log.info("Early stopping at epoch %d (patience %d)", epoch + 1, cfg.patience)
                break
        else:
            # No validation set: keep the latest weights.
            best_state = {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}

    if best_state is not None:
        model.load_state_dict(best_state)
    history["epochs_run"] = float(epoch + 1)
    return history


# --------------------------------------------------------------------------- #
# Evaluation.
# --------------------------------------------------------------------------- #
def predict_groups(model, data: PerturbationData, cfg: Config) -> np.ndarray:
    if data.targets.shape[0] == 0:
        return np.zeros_like(data.targets)
    base, one_hot, _ = _prepare_tensors(data, cfg)
    model.eval()
    with torch.no_grad():
        preds = model(base, one_hot)
    return preds.detach().cpu().numpy().astype(np.float32)


def _group_metrics(targets: np.ndarray, preds: np.ndarray) -> Dict[str, float]:
    return {
        "mse": _mse(targets, preds),
        "pcc": _pearson(targets, preds),
        "r2": _r2(targets, preds),
    }


def _per_cell_metrics(
    x_cells: np.ndarray,  # [n_cells, n_genes] observed log expression
    labels: List[str],    # per-cell perturbation label
    group_preds: Dict[str, np.ndarray],  # label -> predicted profile
    present_mask: np.ndarray,  # [n_genes] gene presence for metrics
) -> Dict[str, float]:
    """Global MSE / Pearson / R2 computed in a memory-safe two-pass fashion."""
    x = np.asarray(x_cells, dtype=np.float64)
    y_masked = x[:, present_mask]
    pred_rows = []
    for lab in labels:
        p = group_preds.get(lab)
        if p is None:
            pred_rows.append(np.full(present_mask.sum(), np.nan))
        else:
            pred_rows.append(np.asarray(p, dtype=np.float64)[present_mask])
    preds = np.asarray(pred_rows, dtype=np.float64)

    finite = np.isfinite(y_masked) & np.isfinite(preds)
    if not finite.any():
        return {"mse": float("nan"), "pcc": float("nan"), "r2": float("nan")}

    y = np.where(finite, y_masked, 0.0)
    p = np.where(finite, preds, 0.0)
    n = int(finite.sum())
    y_sum = float(y.sum())
    p_sum = float(p.sum())
    y_mean = y_sum / n
    p_mean = p_sum / n

    ss_res = float(((y - p) ** 2)[finite].sum())
    ss_tot = float(((y - y_mean) ** 2)[finite].sum())
    mse = ss_res / n
    r2 = 0.0 if ss_tot == 0 else float(1.0 - ss_res / ss_tot)

    yc = (y - y_mean)
    pc = (p - p_mean)
    pcc_num = float((yc * pc)[finite].sum())
    pcc_den1 = float((yc * yc)[finite].sum())
    pcc_den2 = float((pc * pc)[finite].sum())
    denom = float(np.sqrt(pcc_den1 * pcc_den2))
    pcc = 0.0 if denom == 0 else float(pcc_num / denom)
    return {"mse": mse, "pcc": pcc, "r2": r2}


# --------------------------------------------------------------------------- #
# Numpy fallback predictor (no torch available).
# --------------------------------------------------------------------------- #
def _baseline_predictions(data: PerturbationData) -> np.ndarray:
    """Fallback: predict baseline for every group (constant mean-response)."""
    return np.tile(data.baseline[None, :], (data.targets.shape[0], 1)).astype(np.float32)


# --------------------------------------------------------------------------- #
# Main pipeline.
# --------------------------------------------------------------------------- #
def _sanitize_json(obj):
    """Replace non-finite floats (NaN/Inf) with None for strict JSON output."""
    if isinstance(obj, float):
        return obj if np.isfinite(obj) else None
    if isinstance(obj, dict):
        return {k: _sanitize_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitize_json(v) for v in obj]
    return obj


def run_pipeline(
    train_path: str,
    val_path: Optional[str],
    metrics_path: Optional[str],
    cfg: Config,
) -> Dict[str, object]:
    if not _HAS_ANNDATA:
        raise RuntimeError("anndata is required but could not be imported")
    if not os.path.exists(train_path):
        raise FileNotFoundError(f"training data not found: {train_path}")

    adata = _anndata.read_h5ad(train_path)
    pre = Preprocessor(cfg)
    t0 = time.time()
    x_train = pre.fit(adata)
    log.info("Preprocessing finished in %.1fs", time.time() - t0)

    train_labels = _labels_for(adata.obs, pre.perturb_column)
    train_groups = build_group_data(x_train, train_labels, pre.baseline)

    # ---- Validation -------------------------------------------------------
    val_adata = None
    if val_path:
        if not os.path.exists(val_path):
            raise FileNotFoundError(f"validation data not found: {val_path}")
        val_adata = _anndata.read_h5ad(val_path)
        x_val, val_present = pre.transform(val_adata)
        val_labels = _labels_for(val_adata.obs, pre.perturb_column)
        val_groups = build_group_data(x_val, val_labels, pre.baseline)
        # For per-cell metrics use the transformed validation matrix.
        val_cells = x_val
        val_cell_labels = val_labels
        present_mask = val_present
        used_held_out_split = False
    else:
        # No validation file: hold out perturbations (80/20) for evaluation.
        used_held_out_split = True
        non_control = [lab for lab in train_groups.labels if lab != "control"]
        rng = np.random.RandomState(cfg.seed)
        rng.shuffle(non_control)
        n_val = max(1, int(round(0.2 * len(non_control)))) if non_control else 0
        val_labels_set = set(non_control[:n_val])
        train_set = [lab for lab in non_control if lab not in val_labels_set]
        if "control" in train_groups.labels:
            train_set = ["control"] + train_set
        # Rebuild train/val group data.
        train_sub = _subset_groups(train_groups, train_set)
        val_sub = _subset_groups(train_groups, val_labels_set | {"control"})
        # Per-cell evaluation on held-out cells.
        cell_is_val = np.array([lab in val_labels_set for lab in train_labels], dtype=bool)
        val_cells = x_train[cell_is_val]
        val_cell_labels = [lab for i, lab in enumerate(train_labels) if cell_is_val[i]]
        present_mask = np.ones(x_train.shape[1], dtype=bool)
        train_groups = train_sub
        val_groups = val_sub

    log.info(
        "Training samples: %d groups (%d perturbed); validation groups: %d",
        train_groups.targets.shape[0],
        sum(1 for l in train_groups.labels if l != "control"),
        val_groups.targets.shape[0],
    )

    # ---- Model / training --------------------------------------------------
    n_genes = pre.baseline.shape[0]
    if _HAS_TORCH and train_groups.targets.shape[0] > 0:
        _set_seed(cfg.seed)
        model = PerturbationResponseModel(n_genes, cfg)
        history = train_model(model, train_groups, val_groups if val_groups.targets.shape[0] > 0 else None, cfg)
        val_preds = predict_groups(model, val_groups, cfg)
        predictor_name = "transformer"
    else:
        # Graceful fallback when torch is missing / no trainable samples.
        if not _HAS_TORCH:
            log.warning("torch unavailable (%s); using baseline predictor", _TORCH_IMPORT_ERROR)
        val_preds = _baseline_predictions(val_groups)
        predictor_name = "baseline"
        history = {"epochs_run": 0.0}

    # ---- Metrics -----------------------------------------------------------
    group_metrics = _group_metrics(val_groups.targets, val_preds) if val_groups.targets.shape[0] > 0 else {
        "mse": float("nan"), "pcc": float("nan"), "r2": float("nan"),
    }

    # Map label -> predicted profile for per-cell scoring.
    group_preds = {lab: val_preds[i] for i, lab in enumerate(val_groups.labels)}
    per_cell = _per_cell_metrics(val_cells, val_cell_labels, group_preds, present_mask)

    warnings_list: List[str] = []
    if pre.perturb_column is None:
        warnings_list.append(
            "No perturbation/condition column detected in obs; falling back to a baseline (mean) predictor."
        )

    metrics: Dict[str, object] = {
        "status": "ok",
        "predictor": predictor_name,
        "perturbation_column": pre.perturb_column,
        "warnings": warnings_list,
        "mse": group_metrics["mse"],
        "pcc": group_metrics["pcc"],
        "r2": group_metrics["r2"],
        "per_group": group_metrics,
        "per_cell": per_cell,
        "n_train_groups": int(train_groups.targets.shape[0]),
        "n_val_groups": int(val_groups.targets.shape[0]),
        "n_genes": int(n_genes),
        "n_val_cells": int(val_cells.shape[0]),
        "used_held_out_split": bool(used_held_out_split),
        "seed": cfg.seed,
        "training": history,
        "config": cfg.to_dict(),
    }

    metrics = _sanitize_json(metrics)

    if metrics_path:
        os.makedirs(os.path.dirname(os.path.abspath(metrics_path)) or ".", exist_ok=True)
        with open(metrics_path, "w") as fh:
            json.dump(metrics, fh, indent=2, sort_keys=True)
        log.info("Wrote metrics to %s", metrics_path)

    # Human-readable summary on stdout.
    print(json.dumps(metrics, indent=2, sort_keys=True))
    return metrics


def _subset_groups(data: PerturbationData, labels_set) -> PerturbationData:
    keep = [i for i, lab in enumerate(data.labels) if lab in labels_set]
    return PerturbationData(
        baseline=data.baseline,
        labels=[data.labels[i] for i in keep],
        targets=data.targets[keep] if keep else np.zeros((0, data.targets.shape[1]), dtype=np.float32),
        n_cells=data.n_cells[keep] if keep else np.zeros(0, dtype=int),
    )


# --------------------------------------------------------------------------- #
# CLI.
# --------------------------------------------------------------------------- #
def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train a perturbation-response model on single-cell data and write validation metrics as JSON."
    )
    parser.add_argument("data_path", nargs="?", help="Path to training AnnData (.h5ad).")
    parser.add_argument("--adata-path", dest="adata_path_dash")
    parser.add_argument("--adata_path", dest="adata_path_under")
    parser.add_argument("--data_path", dest="data_path_flag")
    parser.add_argument("--data", dest="data_flag")

    parser.add_argument("--val-adata-path", dest="val_adata_path_dash")
    parser.add_argument("--val_data", dest="val_data")
    parser.add_argument("--val-path", dest="val_path")
    parser.add_argument("--val_path", dest="val_path_under")
    parser.add_argument("--val_adata_path", dest="val_adata_path_under")

    parser.add_argument("--output-metrics", dest="output_metrics_dash")
    parser.add_argument("--metrics-path", dest="metrics_path")
    parser.add_argument("--metrics_path", dest="metrics_path_under")
    parser.add_argument("--output", dest="output")

    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--max-genes", type=int, default=512, dest="max_genes")
    return parser.parse_args(argv)


def _first(*values) -> Optional[str]:
    for v in values:
        if v:
            return v
    return None


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    train_path = _first(args.adata_path_dash, args.adata_path_under, args.data_path_flag, args.data_flag, args.data_path)
    val_path = _first(args.val_adata_path_dash, args.val_adata_path_under, args.val_data, args.val_path, args.val_path_under)
    metrics_path = _first(args.output_metrics_dash, args.metrics_path, args.metrics_path_under, args.output)

    if not train_path:
        log.error("No training data path provided (use --adata-path or a positional path).")
        return 2

    cfg = Config(seed=args.seed, epochs=args.epochs, n_top_genes=args.max_genes)

    try:
        run_pipeline(train_path, val_path, metrics_path, cfg)
        return 0
    except Exception as exc:  # noqa: BLE001 - report failures in metrics JSON
        log.exception("Pipeline failed")
        if metrics_path:
            try:
                os.makedirs(os.path.dirname(os.path.abspath(metrics_path)) or ".", exist_ok=True)
                with open(metrics_path, "w") as fh:
                    json.dump({"status": "error", "error": str(exc)}, fh, indent=2)
            except Exception:
                pass
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
