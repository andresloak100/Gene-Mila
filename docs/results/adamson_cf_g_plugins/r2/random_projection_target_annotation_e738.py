import numpy as np
from genemila.features.api import Feature, register


@register
class RandomProjectionTargetAnnotationE738(Feature):
    name = "random_projection_target_annotation_e738"
    version = 1
    description = "Fixed random projection of the target gene's gene_annotation vector (all numeric columns) to 5 dimensions."
    rationale = "Random projections of high-dimensional target annotation may capture latent structure and nonlinear interactions with gene response."
    inputs = ["knowledge"]
    params = {"n_components": 5, "seed": 42}
    dim = 5

    def compute(self, ctx, perts, params):
        n_components = int(params.get("n_components", 5))
        seed = int(params.get("seed", 42))
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, n_components), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is None:
            return out

        cols = ann.get("columns", [])
        genes_ann = ann.get("genes", {})
        if not cols or not genes_ann:
            return out

        # Determine numeric columns: those whose values are numeric (aa_* may be null)
        # Build matrix over annotation genes, keeping only numeric-parseable columns.
        symbols = list(genes_ann.keys())
        if not symbols:
            return out

        # Build raw matrix
        raw = np.full((len(symbols), len(cols)), np.nan, dtype=float)
        for j, c in enumerate(cols):
            for i, s in enumerate(symbols):
                v = genes_ann[s]
                if isinstance(v, dict):
                    v = v.get(c, None)
                elif isinstance(v, (list, tuple)):
                    if j < len(v):
                        v = v[j]
                    else:
                        v = None
                else:
                    v = None
                if v is None:
                    continue
                try:
                    raw[i, j] = float(v)
                except (TypeError, ValueError):
                    raw[i, j] = np.nan

        # Keep columns with at least some numeric data
        valid_cols = np.where(np.any(np.isfinite(raw), axis=0))[0]
        if valid_cols.size == 0:
            return out
        mat = raw[:, valid_cols]

        # Standardize columns (nan-safe): mean/std over finite entries
        col_mean = np.nanmean(mat, axis=0)
        col_std = np.nanstd(mat, axis=0)
        col_std = np.where(col_std > 0, col_std, 1.0)
        mat_std = (mat - col_mean) / col_std
        # Replace remaining NaNs with 0
        mat_std = np.nan_to_num(mat_std, nan=0.0, posinf=0.0, neginf=0.0)

        n_feat = mat_std.shape[1]
        rng = np.random.RandomState(seed)
        proj = rng.randn(n_feat, n_components) / np.sqrt(max(n_feat, 1))

        # Map gene symbol -> row in annotation matrix
        sym_to_row = {s: i for i, s in enumerate(symbols)}

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            if not tg:
                continue
            t = tg[0]
            if t not in sym_to_row:
                continue
            vec = mat_std[sym_to_row[t]]
            proj_vals = vec @ proj  # (n_components,)
            out[i, :, :] = proj_vals[np.newaxis, :]

        return out
