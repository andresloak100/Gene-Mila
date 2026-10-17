import numpy as np
from genemila.features.api import Feature, register

@register
class RBFAnnotationProjectionE606E584(Feature):
    name = "rbf_annotation_projection_e606_e584"
    version = 1
    description = ("Random Fourier features approximating an RBF kernel on standardized "
                   "gene annotation, combined with target annotation/identity.")
    rationale = ("Random Fourier features approximate an RBF kernel over the full "
                 "standardized gene annotation, capturing nonlinear relationships "
                 "and interactions between gene and target annotation.")
    inputs = ["control_cells", "gene_annotation", "targets"]
    params = {"n_components": 50, "gamma": 0.1, "seed": 0}
    dim = 1

    def _build_gene_matrix(self, ctx):
        ann = ctx.knowledge("gene_annotation")
        if ann is None:
            return None, None
        genes_ann = ann.get("genes", {})
        cols = ann.get("columns", [])
        n_cols = len(cols)
        n_genes = ctx.n_genes
        mat = np.zeros((n_genes, n_cols), dtype=float)
        present = np.zeros(n_genes, dtype=bool)
        for i, g in enumerate(ctx.genes):
            vals = genes_ann.get(g)
            if vals is None:
                continue
            row = np.full(n_cols, np.nan, dtype=float)
            for j in range(min(n_cols, len(vals))):
                v = vals[j]
                if v is None:
                    continue
                try:
                    row[j] = float(v)
                except (TypeError, ValueError):
                    pass
            mat[i] = row
            present[i] = True
        # impute nan with column mean over present rows
        if present.any():
            col_mean = np.nanmean(np.where(present[:, None], mat, np.nan), axis=0)
            col_mean = np.where(np.isfinite(col_mean), col_mean, 0.0)
        else:
            col_mean = np.zeros(n_cols)
        inds = np.where(~np.isfinite(mat))
        mat[inds] = np.take(col_mean, inds[1])
        # standardize
        mu = mat.mean(axis=0)
        sd = mat.std(axis=0)
        sd = np.where(sd > 1e-8, sd, 1.0)
        mat = (mat - mu) / sd
        return mat, cols

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        n_perts = len(perts)
        out = np.zeros((n_perts, n_genes, 1), dtype=float)

        n_comp = int(params.get("n_components", 50))
        gamma = float(params.get("gamma", 0.1))
        seed = int(params.get("seed", 0))

        key = ("rbf_ann_e606", n_comp, gamma, seed)
        cache = ctx.cache
        if key in cache:
            rff = cache[key]
        else:
            mat, _ = self._build_gene_matrix(ctx)
            if mat is None or mat.size == 0:
                cache[key] = None
                rff = None
            else:
                d = mat.shape[1]
                rng = np.random.RandomState(seed)
                W = rng.normal(0.0, np.sqrt(2.0 * gamma), size=(d, n_comp))
                b = rng.uniform(0.0, 2.0 * np.pi, size=n_comp)
                proj = mat @ W + b[None, :]
                rff = np.cos(proj) * np.sqrt(2.0 / n_comp)
                cache[key] = rff

        if rff is None:
            return out

        # target rff per perturbation
        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if t_idx:
                t_vec = rff[t_idx].mean(axis=0)
            else:
                t_vec = np.zeros(rff.shape[1], dtype=float)
            # combine gene rff with target rff via dot product
            out[i, :, 0] = rff @ t_vec

        return out
