import numpy as np
from genemila.features.api import Feature, register


@register
class GeneAnnotationRandomProjectionE736(Feature):
    name = "gene_annotation_random_projection_e736"
    version = 1
    description = ("Random Gaussian projection of standardized per-gene gene_annotation "
                   "numeric features into a low-dimensional space.")
    rationale = ("Gene annotation contains many correlated numeric features; a random "
                 "projection summarizes them into a few components that may capture "
                 "structure beyond individual annotation features.")
    inputs = ["knowledge:gene_annotation"]
    params = {"n_components": 10, "random_seed": 42}
    dim = 10

    def compute(self, ctx, perts, params):
        n_components = int(params.get("n_components", 10))
        seed = int(params.get("random_seed", 42))
        self.dim = n_components

        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, n_components), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is None:
            return out

        genes_ann = ann.get("genes") or {}
        columns = ann.get("columns") or []

        # Build (n_genes, n_features) matrix from numeric annotation columns.
        mat = np.full((n_genes, len(columns)), np.nan, dtype=float)
        for gi, g in enumerate(ctx.genes):
            vals = genes_ann.get(g)
            if not vals:
                continue
            for ci in range(min(len(columns), len(vals))):
                v = vals[ci]
                if isinstance(v, (int, float)) and np.isfinite(v):
                    mat[gi, ci] = float(v)

        # Keep only columns with some finite data.
        finite_counts = np.isfinite(mat).sum(axis=0)
        keep = finite_counts >= max(2, n_genes // 100)
        if not np.any(keep):
            return out
        mat = mat[:, keep]
        n_feat = mat.shape[1]

        # Impute missing with column mean, standardize.
        col_mean = np.nanmean(mat, axis=0)
        col_std = np.nanstd(mat, axis=0)
        col_std = np.where(col_std > 1e-12, col_std, 1.0)
        inds = np.where(~np.isfinite(mat))
        mat[inds] = np.take(col_mean, inds[1])
        Z = (mat - col_mean) / col_std
        Z = np.nan_to_num(Z, nan=0.0, posinf=0.0, neginf=0.0)

        # Random Gaussian projection matrix.
        rng = np.random.default_rng(seed)
        R = rng.standard_normal((n_feat, n_components)) / np.sqrt(max(n_feat, 1))
        proj = Z @ R  # (n_genes, n_components)

        # Same per-gene vector for every perturbation row.
        out[:] = proj[None, :, :]
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
