import numpy as np
from genemila.features.api import Feature, register


@register
class TargetAnnotationRandomProjectionE201(Feature):
    name = "target_annotation_random_projection_e201"
    version = 1
    description = "Random projection of all gene annotation features for the perturbation's target gene into 5 dimensions."
    rationale = (
        "Target-level annotations may encode biological information not captured by "
        "individual features; a random projection aggregates them into a few latent dimensions."
    )
    inputs = ["knowledge:gene_annotation", "target_indices"]
    params = {"n_components": 5}
    dim = 5

    def compute(self, ctx, perts, params):
        n_comp = int(params.get("n_components", 5))
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, n_comp), dtype=float)

        ga = ctx.knowledge("gene_annotation")
        if not ga or "genes" not in ga or "columns" not in ga:
            return out

        columns = list(ga["columns"])
        genes_dict = ga["genes"]
        n_feat = len(columns)

        # Build feature matrix (n_genes x n_feat), median-fill missing.
        mat = np.full((n_genes, n_feat), np.nan, dtype=float)
        for gi, gname in enumerate(ctx.genes):
            vals = genes_dict.get(gname)
            if vals is None:
                continue
            if isinstance(vals, dict):
                row = [vals.get(c) for c in columns]
            else:
                row = list(vals)
            for fi in range(min(n_feat, len(row))):
                v = row[fi]
                if v is None:
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv):
                    mat[gi, fi] = fv

        # Median-fill each column; fill remaining with 0.
        for fi in range(n_feat):
            col = mat[:, fi]
            finite = np.isfinite(col)
            if finite.any():
                med = np.nanmedian(col[finite])
            else:
                med = 0.0
            col[~finite] = med
            mat[:, fi] = col

        # Standardise columns (avoid div by zero).
        mu = mat.mean(axis=0)
        sd = mat.std(axis=0)
        sd[sd < 1e-8] = 1.0
        mat = (mat - mu) / sd

        # Fixed random projection matrix (n_feat x n_comp), deterministic seed.
        rng = np.random.RandomState(201)
        proj = rng.normal(0.0, 1.0 / np.sqrt(max(n_feat, 1)), size=(n_feat, n_comp))

        # Projected target vectors per gene.
        projected = mat @ proj  # (n_genes, n_comp)

        # Cache per-target projected vectors.
        cache = ctx.cache
        key = "_e201_target_proj"
        if key not in cache:
            cache[key] = {}
        tcache = cache[key]

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            # Average projection over target genes (usually 1).
            vec = projected[tgt_idx].mean(axis=0)
            out[i, :, :] = vec[None, :]

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
