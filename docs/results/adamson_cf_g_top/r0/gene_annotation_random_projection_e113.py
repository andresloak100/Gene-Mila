import numpy as np
from genemila.features.api import Feature, register


@register
class GeneAnnotationRandomProjection(Feature):
    name = "gene_annotation_random_projection_e113"
    version = 1
    description = "Random Gaussian projection of standardized per-gene annotation vectors."
    rationale = (
        "Gene annotation vectors encode rich structure; a fixed random low-dimensional "
        "projection captures latent biological similarity without overfitting."
    )
    inputs = ["knowledge:gene_annotation"]
    params = {"n_components": 10, "random_seed": 42}
    dim = 10

    def compute(self, ctx, perts, params):
        n_comp = int(params.get("n_components", 10))
        seed = int(params.get("random_seed", 42))
        n_genes = ctx.n_genes

        out = np.zeros((len(perts), n_genes, n_comp), dtype=float)

        cache_key = ("gene_annotation_random_projection_e113", n_comp, seed)
        if cache_key in ctx.cache:
            proj = ctx.cache[cache_key]
        else:
            ann = ctx.knowledge("gene_annotation")
            proj = np.zeros((n_genes, n_comp), dtype=float)
            if ann is not None and isinstance(ann, dict):
                genes_map = ann.get("genes", {}) or {}
                columns = ann.get("columns", []) or []
                n_feat = len(columns)
                if n_feat > 0:
                    mat = np.full((n_genes, n_feat), np.nan, dtype=float)
                    for gi, g in enumerate(ctx.genes):
                        vals = genes_map.get(g)
                        if vals is None:
                            continue
                        for fi in range(min(n_feat, len(vals))):
                            v = vals[fi]
                            if v is None:
                                continue
                            try:
                                fv = float(v)
                            except (TypeError, ValueError):
                                continue
                            if np.isfinite(fv):
                                mat[gi, fi] = fv
                    # column means / stds over finite entries
                    col_mean = np.zeros(n_feat, dtype=float)
                    col_std = np.ones(n_feat, dtype=float)
                    for fi in range(n_feat):
                        col = mat[:, fi]
                        finite = np.isfinite(col)
                        if finite.any():
                            m = col[finite].mean()
                            s = col[finite].std()
                            col_mean[fi] = m
                            col_std[fi] = s if s > 1e-8 else 1.0
                    # standardize; missing -> 0
                    std_mat = np.zeros_like(mat)
                    for fi in range(n_feat):
                        col = mat[:, fi]
                        finite = np.isfinite(col)
                        std_mat[finite, fi] = (col[finite] - col_mean[fi]) / col_std[fi]
                    rng = np.random.default_rng(seed)
                    W = rng.standard_normal((n_feat, n_comp))
                    proj = std_mat @ W
                    proj = np.nan_to_num(proj, nan=0.0, posinf=0.0, neginf=0.0)
            ctx.cache[cache_key] = proj

        # same per-gene projection for every perturbation row
        for i in range(len(perts)):
            out[i, :, :] = proj

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
