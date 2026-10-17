import numpy as np
from genemila.features.api import Feature, register


@register
class CombinedAnnotationProjectionTargetInteraction(Feature):
    name = "combined_annotation_projection_target_in_e398"
    version = 1
    description = (
        "Dot product between random projections of concatenated (standardized) gene and "
        "protein annotation vectors for the perturbation target and gene g."
    )
    rationale = (
        "Random projection of combined gene + protein annotation captures functional "
        "similarity between target and gene beyond single-annotation projections."
    )
    inputs = ["knowledge", "target_indices"]
    params = {"projection_dim": 50, "seed": 398}
    dim = 1

    def _build_matrix(self, ctx, params):
        cache = ctx.cache
        key = ("e398_matrix", params.get("projection_dim", 50), params.get("seed", 398))
        if key in cache:
            return cache[key]

        n_genes = ctx.n_genes
        gene_idx = ctx.gene_index
        cols = []

        # --- gene_annotation ---
        ga = ctx.knowledge("gene_annotation")
        if ga is not None:
            gcols = ga.get("columns", [])
            ggenes = ga.get("genes", {})
            mat = np.full((n_genes, len(gcols)), np.nan, dtype=np.float64)
            for sym, vals in ggenes.items():
                j = gene_idx.get(sym)
                if j is None:
                    continue
                for c, v in enumerate(vals):
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        mat[j, c] = fv
            cols.append(mat)

        # --- protein_annotation ---
        pa = ctx.knowledge("protein_annotation")
        if pa is not None:
            pcols = pa.get("columns", [])
            pgenes = pa.get("genes", {})
            mat = np.full((n_genes, len(pcols)), np.nan, dtype=np.float64)
            for sym, vals in pgenes.items():
                j = gene_idx.get(sym)
                if j is None:
                    continue
                for c, v in enumerate(vals):
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        mat[j, c] = fv
            cols.append(mat)

        if not cols:
            mat = np.zeros((n_genes, 1), dtype=np.float64)
        else:
            mat = np.concatenate(cols, axis=1)

        # standardize each column (nan-safe)
        mu = np.nanmean(mat, axis=0)
        sd = np.nanstd(mat, axis=0)
        mu = np.where(np.isfinite(mu), mu, 0.0)
        sd = np.where(np.isfinite(sd) & (sd > 1e-12), sd, 1.0)
        mat = (mat - mu) / sd
        mat = np.where(np.isfinite(mat), mat, 0.0)

        d = int(params.get("projection_dim", 50))
        seed = int(params.get("seed", 398))
        rng = np.random.RandomState(seed)
        R = rng.randn(mat.shape[1], d) / np.sqrt(max(mat.shape[1], 1))
        proj = mat @ R  # (n_genes, d)

        cache[key] = proj
        return proj

    def compute(self, ctx, perts, params):
        proj = self._build_matrix(ctx, params)
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=np.float64)
        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if not t_idx:
                continue
            tvec = proj[t_idx].mean(axis=0)  # (d,)
            out[i, :, 0] = proj @ tvec
        out = np.where(np.isfinite(out), out, 0.0)
        return out
