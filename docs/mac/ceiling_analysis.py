"""How high can pearson_delta go on this dataset? A free, offline check on TRAINING perturbations only.

Uses the public bundle (control cells, training means, gene list) and the raw 10X010 file for the
cells of training perturbations. It never opens data/*/private or splits.json.

1. Noise ceiling: split each training perturbation's cells in two random halves; the correlation
   between the two halves' deltas gives the reliability of a measured delta, and
   sqrt(Spearman-Brown reliability) is the most a perfect predictor could score against it.
2. Transfer ceiling: the best pearson_delta any model can reach if all it may do is combine the
   deltas of the OTHER training perturbations (oracle weights fitted on the truth itself).
3. Where the simple predictors sit against those two ceilings.
"""
import json
import sys
from pathlib import Path

import anndata as ad
import numpy as np
import scipy.sparse as sp
from scipy.optimize import nnls

REPO = Path.home() / "Documents/Mila/Gene-Mila/gene-mila"
pub = np.load(REPO / "data/adamson_cf/public.npz", allow_pickle=False)
genes = [str(g) for g in pub["genes"]]
train = [str(p) for p in pub["train_perts"]]
ctrl_mean = pub["control_cells"].astype(np.float64).mean(axis=0)
T = pub["train_means"].astype(np.float64) - ctrl_mean          # training deltas, perts x genes
n, G = T.shape
rng = np.random.default_rng(0)


def pear(a, b):
    a = a - a.mean(); b = b - b.mean()
    d = np.sqrt((a * a).sum() * (b * b).sum())
    return float((a * b).sum() / d) if d > 0 else 0.0


# ---- 1. noise ceiling from the raw cells of training perturbations
a = ad.read_h5ad(REPO / "data/raw/AdamsonWeissman2016_GSM2406681_10X010.h5ad")
X = sp.csr_matrix(a.X, dtype=np.float32)
tot = np.asarray(X.sum(axis=1)).ravel()
X = sp.diags((1e4 / np.where(tot > 0, tot, 1)).astype(np.float32)) @ X
X.data = np.log1p(X.data)
X = X.tocsc()[:, [list(a.var_names).index(g) for g in genes]].tocsr()
lab = a.obs["perturbation"].astype(object).fillna("unassigned").to_numpy(dtype=str)
gene_of = np.array([l.split("_")[0] for l in lab])

rows = []
for i, p in enumerate(train):
    idx = np.flatnonzero(gene_of == p)
    if len(idx) < 40:
        continue
    # check our reconstruction of the perturbation mean against the bundle's
    full = np.asarray(X[idx].mean(axis=0)).ravel() - ctrl_mean
    rec = pear(full, T[i])
    rs = []
    for _ in range(20):
        perm = rng.permutation(idx); h = len(perm) // 2
        d1 = np.asarray(X[perm[:h]].mean(axis=0)).ravel() - ctrl_mean
        d2 = np.asarray(X[perm[h:]].mean(axis=0)).ravel() - ctrl_mean
        rs.append(pear(d1, d2))
    r = float(np.mean(rs))
    rel = 2 * r / (1 + r) if r > -1 else 0.0          # reliability of the full-sample delta
    rows.append({"pert": p, "n_cells": int(len(idx)), "recon_r": rec, "split_half_r": r,
                 "reliability": rel, "noise_ceiling": float(np.sqrt(max(rel, 0)))})

# ---- 2 and 3. what can be predicted from the other training perturbations
loo_mean, best_single, oracle_nnls, oracle_ols, strength = [], [], [], [], []
for i in range(n):
    others = np.delete(np.arange(n), i)
    A = T[others].T                                   # genes x (n-1)
    y = T[i]
    loo_mean.append(pear(A.mean(axis=1), y))
    best_single.append(max(pear(A[:, j], y) for j in range(A.shape[1])))
    w, _ = nnls(A, y); oracle_nnls.append(pear(A @ w, y))
    w2, *_ = np.linalg.lstsq(A, y, rcond=None); oracle_ols.append(pear(A @ w2, y))
    strength.append(float(np.sqrt((y * y).mean())))

by = {r["pert"]: r for r in rows}
ceil = np.array([by[p]["noise_ceiling"] for p in train if p in by])
out = {
    "n_train": n, "n_genes": G, "n_with_cells": len(rows),
    "recon_r_min": float(min(r["recon_r"] for r in rows)),
    "noise_ceiling_mean": float(ceil.mean()), "noise_ceiling_median": float(np.median(ceil)),
    "noise_ceiling_min": float(ceil.min()), "noise_ceiling_max": float(ceil.max()),
    "split_half_r_mean": float(np.mean([r["split_half_r"] for r in rows])),
    "loo_mean_response": float(np.mean(loo_mean)),
    "oracle_best_single_neighbour": float(np.mean(best_single)),
    "oracle_nonneg_combination": float(np.mean(oracle_nnls)),
    "oracle_any_linear_combination": float(np.mean(oracle_ols)),
    "per_pert": [{"pert": p, "n_cells": by.get(p, {}).get("n_cells"), "strength_rms_delta": strength[i],
                  "noise_ceiling": by.get(p, {}).get("noise_ceiling"), "loo_mean": loo_mean[i],
                  "best_single": best_single[i], "oracle_nnls": oracle_nnls[i]} for i, p in enumerate(train)],
}
Path(sys.argv[1] if len(sys.argv) > 1 else "ceiling_analysis.json").write_text(json.dumps(out, indent=1))
print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in out.items() if k != "per_pert"})
print("pert | cells | rms delta | noise ceiling | LOO mean | best single | oracle nnls")
for r in sorted(out["per_pert"], key=lambda r: r["loo_mean"]):
    print(f"{r['pert']:10s} {str(r['n_cells']):>5s} {r['strength_rms_delta']:.4f} "
          f"{(r['noise_ceiling'] or float('nan')):.3f} {r['loo_mean']:.3f} {r['best_single']:.3f} {r['oracle_nnls']:.3f}")
