import numpy as np
from genemila.features.api import Feature, register


@register
class FullAnnotationProjectionTargetE459(Feature):
    name = "full_annotation_projection_target_e459"
    version = 1
    description = (
        "Dot product between random projections of the full standardized gene "
        "annotation vector (all columns) for the perturbation target and for gene g."
    )
    rationale = (
        "Full annotation vectors (including amino-acid fractions and structural "
        "features) may capture additional biological similarity between target and "
        "gene beyond a subset-based projection."
    )
    inputs = ["knowledge:gene_annotation", "target_indices"]
    params = {"n_components": 20, "seed": 0}
    dim = 1

    def compute(self, ctx, perts, params):
        n_comp = int(params.get("n_components", 20))
        seed = int(params.get("seed", 0))

        cache = ctx.cache
        key = ("full_annot_proj", n_comp, seed)
        if key not in cache:
            cache[key] = self._build_projections(ctx, n_comp, seed)
        proj = cache[key]  # (n_genes, n_comp)

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            tidx = ctx.target_indices(p)
            if not tidx:
                continue
            tproj = proj[tidx].mean(axis=0)  # (n_comp,)
            out[i, :, 0] = proj @ tproj

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out

    def _build_projections(self, ctx, n_comp, seed):
        ann = ctx.knowledge("gene_annotation")
        n_genes = ctx.n_genes

        mat = np.zeros((n_genes, 0), dtype=float)
        if ann is not None and isinstance(ann, dict):
            genes_tbl = ann.get("genes", {}) or {}
            columns = ann.get("columns", []) or []
            n_cols = len(columns)
            if n_cols > 0:
                mat = np.full((n_genes, n_cols), np.nan, dtype=float)
                for gi, g in enumerate(ctx.genes):
                    vals = genes_tbl.get(g)
                    if vals is None:
                        continue
                    row = np.full(n_cols, np.nan, dtype=float)
                    m = min(len(vals), n_cols)
                    for j in range(m):
                        v = vals[j]
                        if v is None:
                            continue
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv):
                            row[j] = fv
                    mat[gi, :] = row

        if mat.shape[1] == 0:
            # No usable annotation: fall back to a single constant column so the
            # feature still returns finite values.
            mat = np.zeros((n_genes, 1), dtype=float)

        # Impute missing with column means; columns all-missing -> 0.
        col_mean = np.nanmean(mat, axis=0)
        col_mean = np.where(np.isfinite(col_mean), col_mean, 0.0)
        inds = np.where(~np.isfinite(mat))
        if inds[0].size > 0:
            mat[inds] = np.take(col_mean, inds[1])

        # Standardize columns.
        mu = mat.mean(axis=0)
        sd = mat.std(axis=0)
        sd = np.where(sd > 1e-12, sd, 1.0)
        mat = (mat - mu) / sd

        # Fixed random projection.
        rng = np.random.RandomState(seed)
        R = rng.randn(mat.shape[1], n_comp) / np.sqrt(max(mat.shape[1], 1))
        proj = mat @ R  # (n_genes, n_comp)
        proj = np.nan_to_num(proj, nan=0.0, posinf=0.0, neginf=0.0)
        return proj
