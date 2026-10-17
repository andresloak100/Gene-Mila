import numpy as np
from genemila.features.api import Feature, register


@register
class GeneAnnotationRandomProjectionTanh(Feature):
    name = "gene_annotation_random_projection_tanh_e572"
    version = 1
    description = ("Fixed random projection of static gene annotation features "
                   "(gene_annotation + protein_annotation) to n_components dims, "
                   "tanh-transformed, concatenated with the target gene's projection.")
    rationale = ("Random projections combine many weak static annotation signals; "
                 "tanh adds nonlinearity so interactions may be captured.")
    inputs = ["knowledge"]
    params = {"n_components": 10, "seed": 42}
    dim = 20

    def _build_matrix(self, ctx, params):
        key = ("garp_matrix", params.get("n_components", 10), params.get("seed", 42))
        cache = ctx.cache
        if key in cache:
            return cache[key]

        n_comp = int(params.get("n_components", 10))
        seed = int(params.get("seed", 42))

        ga = ctx.knowledge("gene_annotation")
        pa = ctx.knowledge("protein_annotation")

        n_genes = ctx.n_genes
        feats = []

        # gene_annotation numeric columns
        ga_cols = None
        ga_genes = None
        if isinstance(ga, dict):
            ga_cols = ga.get("columns", None)
            ga_genes = ga.get("genes", None)
        if ga_cols is not None and ga_genes is not None:
            # identify numeric columns (skip aa_* which may be null but are numeric)
            numeric_idx = []
            for j, c in enumerate(ga_cols):
                cl = str(c).lower()
                if cl.startswith("aa_"):
                    numeric_idx.append(j)
                else:
                    numeric_idx.append(j)  # all listed are numeric per spec
            mat = np.full((n_genes, len(numeric_idx)), np.nan, dtype=np.float64)
            for gi, g in enumerate(ctx.genes):
                vals = ga_genes.get(g, None)
                if vals is None:
                    continue
                for k, j in enumerate(numeric_idx):
                    if j < len(vals) and vals[j] is not None:
                        try:
                            mat[gi, k] = float(vals[j])
                        except (TypeError, ValueError):
                            pass
            feats.append(mat)

        # protein_annotation numeric columns
        if isinstance(pa, dict):
            pa_cols = pa.get("columns", None)
            pa_genes = pa.get("genes", None)
            if pa_cols is not None and pa_genes is not None:
                mat = np.full((n_genes, len(pa_cols)), np.nan, dtype=np.float64)
                for gi, g in enumerate(ctx.genes):
                    vals = pa_genes.get(g, None)
                    if vals is None:
                        continue
                    for j in range(len(pa_cols)):
                        if j < len(vals) and vals[j] is not None:
                            try:
                                mat[gi, j] = float(vals[j])
                            except (TypeError, ValueError):
                                pass
                feats.append(mat)

        if not feats:
            # fallback: use control_mean/std as annotation proxy
            feats = [ctx.control_mean.reshape(-1, 1),
                     ctx.control_std.reshape(-1, 1)]

        X = np.concatenate(feats, axis=1)
        # replace nan with column mean, then standardize
        col_mean = np.nanmean(X, axis=0)
        col_mean = np.where(np.isfinite(col_mean), col_mean, 0.0)
        inds = np.where(~np.isfinite(X))
        X[inds] = np.take(col_mean, inds[1])

        mu = X.mean(axis=0)
        sd = X.std(axis=0)
        sd = np.where(sd > 1e-8, sd, 1.0)
        Xs = (X - mu) / sd

        rng = np.random.RandomState(seed)
        W = rng.randn(Xs.shape[1], n_comp) / np.sqrt(max(Xs.shape[1], 1))

        proj = np.tanh(Xs @ W)  # (n_genes, n_comp)

        cache[key] = proj
        return proj

    def compute(self, ctx, perts, params):
        proj = self._build_matrix(ctx, params)
        n_comp = proj.shape[1]
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 2 * n_comp), dtype=np.float64)

        for i, p in enumerate(perts):
            out[i, :, :n_comp] = proj
            t_idx = ctx.target_indices(p)
            if t_idx:
                tproj = proj[t_idx].mean(axis=0)
            else:
                tproj = np.zeros(n_comp, dtype=np.float64)
            out[i, :, n_comp:] = tproj

        return out
