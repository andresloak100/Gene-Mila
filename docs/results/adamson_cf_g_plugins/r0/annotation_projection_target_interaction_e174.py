import numpy as np
from genemila.features.api import Feature, register


@register
class AnnotationProjectionTargetInteraction(Feature):
    name = "annotation_projection_target_interaction_e174"
    version = 1
    description = ("Dot product between random projections of gene annotation vectors "
                   "for the perturbation target and each gene, using multiple components.")
    rationale = ("A low-dimensional random projection of gene annotation, interacted with the "
                 "target's annotation projection, may capture nonlinear gene-target relationships "
                 "beyond what the projection alone provides.")
    inputs = ["gene_annotation"]
    params = {"n_components": 10, "seed": 174}
    dim = 1

    def compute(self, ctx, perts, params):
        n_components = int(params.get("n_components", 10))
        seed = int(params.get("seed", 174))
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is None:
            return out

        genes_tbl = ann.get("genes", {})
        columns = ann.get("columns", [])
        if not genes_tbl or not columns:
            return out

        # Build annotation matrix in ctx.genes order.
        n_cols = len(columns)
        mat = np.zeros((n_genes, n_cols), dtype=float)
        present = np.zeros(n_genes, dtype=bool)
        for i, g in enumerate(ctx.genes):
            vals = genes_tbl.get(g)
            if vals is None:
                continue
            row = np.full(n_cols, np.nan, dtype=float)
            m = min(n_cols, len(vals))
            for j in range(m):
                v = vals[j]
                if v is None:
                    continue
                try:
                    row[j] = float(v)
                except (TypeError, ValueError):
                    row[j] = np.nan
            mat[i] = row
            present[i] = True

        if not present.any():
            return out

        # Impute missing values with column means over present rows.
        col_mean = np.zeros(n_cols, dtype=float)
        for j in range(n_cols):
            col = mat[present, j]
            finite = np.isfinite(col)
            if finite.any():
                col_mean[j] = col[finite].mean()
            else:
                col_mean[j] = 0.0
        nan_mask = ~np.isfinite(mat)
        if nan_mask.any():
            mat[nan_mask] = np.take(col_mean, np.where(nan_mask)[1])

        # Standardize columns.
        mu = mat.mean(axis=0)
        sd = mat.std(axis=0)
        sd[sd < 1e-8] = 1.0
        mat = (mat - mu) / sd

        # Random projection matrix.
        rng = np.random.RandomState(seed)
        proj = rng.randn(n_cols, n_components) / np.sqrt(max(n_cols, 1))
        gene_proj = mat @ proj  # (n_genes, n_components)

        # For each perturbation, get target projection and dot with all genes.
        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if not t_idx:
                continue
            t_idx = [t for t in t_idx if 0 <= t < n_genes]
            if not t_idx:
                continue
            target_proj = gene_proj[t_idx].mean(axis=0)  # (n_components,)
            out[i, :, 0] = gene_proj @ target_proj

        out[~np.isfinite(out)] = 0.0
        return out
