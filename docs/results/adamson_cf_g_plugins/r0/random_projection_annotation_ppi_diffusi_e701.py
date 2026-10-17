import numpy as np
from genemila.features.api import Feature, register


@register
class RandomProjectionAnnotationPPIDiffusionE701(Feature):
    name = "random_projection_annotation_ppi_diffusi_e701"
    version = 1
    description = ("Random Gaussian projection of concatenated standardized gene annotation "
                   "features and PPI diffusion scores from perturbation target to gene.")
    rationale = ("Random projections can capture complex interactions between annotation and "
                 "network-diffusion signals without explicit feature engineering.")
    inputs = ["control_mean", "knowledge", "target_indices"]
    params = {"projection_dim": 20, "seed": 42, "diffusion_alpha": 0.5, "diffusion_steps": 2}
    dim = 20

    # ---- helpers ---------------------------------------------------------
    def _annotation_matrix(self, ctx, params):
        cache = ctx.cache
        key = "e701_annot_matrix"
        if key in cache:
            return cache[key]
        ann = ctx.knowledge("gene_annotation")
        n = ctx.n_genes
        if ann is None or "genes" not in ann or "columns" not in ann:
            mat = np.zeros((n, 0), dtype=np.float64)
            cache[key] = mat
            return mat
        cols = list(ann["columns"])
        genes = ann["genes"]
        mat = np.full((n, len(cols)), np.nan, dtype=np.float64)
        for gi, g in enumerate(ctx.genes):
            vals = genes.get(g)
            if vals is None:
                continue
            for cj in range(min(len(cols), len(vals))):
                v = vals[cj]
                if v is None:
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv):
                    mat[gi, cj] = fv
        # standardize columns (nan-aware); fill nan with 0 after centering
        if mat.shape[1] > 0:
            col_mean = np.nanmean(mat, axis=0)
            col_std = np.nanstd(mat, axis=0)
            col_mean = np.where(np.isfinite(col_mean), col_mean, 0.0)
            col_std = np.where(np.isfinite(col_std) & (col_std > 1e-8), col_std, 1.0)
            mat = (mat - col_mean) / col_std
            mat = np.where(np.isfinite(mat), mat, 0.0)
        cache[key] = mat
        return mat

    def _adjacency(self, ctx):
        cache = ctx.cache
        key = "e701_adj"
        if key in cache:
            return cache[key]
        n = ctx.n_genes
        A = np.zeros((n, n), dtype=np.float64)
        ppi = ctx.knowledge("ppi_network")
        if ppi:
            gi = ctx.gene_index
            for entry in ppi:
                if len(entry) < 3:
                    continue
                a, b, w = entry[0], entry[1], entry[2]
                ia = gi.get(a)
                ib = gi.get(b)
                if ia is None or ib is None:
                    continue
                try:
                    wv = float(w)
                except (TypeError, ValueError):
                    continue
                if not np.isfinite(wv):
                    continue
                A[ia, ib] = wv
                A[ib, ia] = wv
        # row-normalize (random-walk style)
        rs = A.sum(axis=1, keepdims=True)
        rs = np.where(rs > 1e-12, rs, 1.0)
        A = A / rs
        cache[key] = A
        return A

    def _diffusion_scores(self, ctx, target_idx, params):
        A = self._adjacency(ctx)
        alpha = float(params.get("diffusion_alpha", 0.5))
        steps = int(params.get("diffusion_steps", 2))
        n = ctx.n_genes
        v = np.zeros(n, dtype=np.float64)
        v[target_idx] = 1.0
        out = v.copy()
        cur = v
        for _ in range(max(1, steps)):
            cur = alpha * (A.T @ cur) + (1.0 - alpha) * v
            out = out + cur
        return out

    def _random_matrix(self, ctx, in_dim, out_dim, seed):
        cache = ctx.cache
        key = ("e701_proj", in_dim, out_dim, seed)
        if key in cache:
            return cache[key]
        rng = np.random.RandomState(int(seed))
        W = rng.randn(in_dim, out_dim) / np.sqrt(max(in_dim, 1))
        cache[key] = W
        return W

    # ---- main ------------------------------------------------------------
    def compute(self, ctx, perts, params):
        out_dim = int(params.get("projection_dim", 20))
        seed = int(params.get("seed", 42))
        ann = self._annotation_matrix(ctx, params)
        n = ctx.n_genes
        n_ann = ann.shape[1]

        out = np.zeros((len(perts), n, out_dim), dtype=np.float64)

        for i, p in enumerate(perts):
            tgt = ctx.target_indices(p)
            if len(tgt) == 0:
                continue
            diff = self._diffusion_scores(ctx, tgt, params)
            # standardize diffusion
            dstd = diff.std()
            if dstd > 1e-12:
                diff = (diff - diff.mean()) / dstd
            else:
                diff = diff - diff.mean()

            if n_ann > 0:
                feat = np.concatenate([ann, diff[:, None]], axis=1)
            else:
                feat = diff[:, None]

            W = self._random_matrix(ctx, feat.shape[1], out_dim, seed)
            proj = feat @ W
            out[i] = proj

        out = np.where(np.isfinite(out), out, 0.0)
        return out
