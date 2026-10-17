import numpy as np
from genemila.features.api import Feature, register


@register
class GeneAnnotationRandomProjectionE680(Feature):
    name = "gene_annotation_random_projection_e680"
    version = 1
    description = "Random projection of concatenated gene annotation features, compared to target average projection."
    rationale = "A compressed random projection of annotation features may capture latent biological signal without overfitting."
    inputs = ["knowledge"]
    params = {"k": 20}
    dim = 1

    def _build_matrix(self, ctx, params):
        k = int(params.get("k", 20))
        genes = ctx.genes
        n = len(genes)
        gi = ctx.gene_index

        blocks = []

        ann = ctx.knowledge("gene_annotation")
        if ann and "genes" in ann:
            cols = ann.get("columns", [])
            gd = ann["genes"]
            mat = np.full((n, len(cols)), np.nan)
            for i, g in enumerate(genes):
                vals = gd.get(g)
                if vals is not None:
                    for j, v in enumerate(vals[:len(cols)]):
                        try:
                            mat[i, j] = float(v)
                        except (TypeError, ValueError):
                            mat[i, j] = np.nan
            blocks.append(mat)

        con = ctx.knowledge("gene_constraint")
        if con and "genes" in con:
            cols = con.get("columns", [])
            gd = con["genes"]
            mat = np.full((n, len(cols)), np.nan)
            for i, g in enumerate(genes):
                vals = gd.get(g)
                if vals is not None:
                    for j, v in enumerate(vals[:len(cols)]):
                        try:
                            mat[i, j] = float(v)
                        except (TypeError, ValueError):
                            mat[i, j] = np.nan
            blocks.append(mat)

        prot = ctx.knowledge("protein_annotation")
        if prot and "genes" in prot:
            cols = prot.get("columns", [])
            gd = prot["genes"]
            mat = np.full((n, len(cols)), np.nan)
            for i, g in enumerate(genes):
                vals = gd.get(g)
                if vals is not None:
                    for j, v in enumerate(vals[:len(cols)]):
                        try:
                            mat[i, j] = float(v)
                        except (TypeError, ValueError):
                            mat[i, j] = np.nan
            blocks.append(mat)

        if not blocks:
            return np.zeros((n, k)), k

        X = np.concatenate(blocks, axis=1)
        # standardize columns, fill nan with mean
        col_mean = np.nanmean(X, axis=0)
        col_mean = np.where(np.isfinite(col_mean), col_mean, 0.0)
        inds = np.where(~np.isfinite(X))
        X[inds] = np.take(col_mean, inds[1])
        col_std = X.std(axis=0)
        col_std = np.where(col_std > 1e-8, col_std, 1.0)
        X = (X - col_mean) / col_std

        D = X.shape[1]
        rng = np.random.RandomState(680)
        R = rng.randn(D, k) / np.sqrt(D)
        P = X @ R  # (n, k)
        return P, k

    def compute(self, ctx, perts, params):
        k = int(params.get("k", 20))
        if "proj" not in ctx.cache:
            P, k = self._build_matrix(ctx, params)
            ctx.cache["proj"] = P
            ctx.cache["proj_k"] = k
        P = ctx.cache["proj"]

        out = np.zeros((len(perts), ctx.n_genes, 1))
        for i, p in enumerate(perts):
            tidx = ctx.target_indices(p)
            if tidx:
                tavg = P[tidx].mean(axis=0)
            else:
                tavg = np.zeros(P.shape[1])
            out[i, :, 0] = P @ tavg
        out[~np.isfinite(out)] = 0.0
        return out
