import numpy as np
from genemila.features.api import Feature, register


@register
class StaticAnnotationRandomProjectionE530(Feature):
    name = "static_annotation_random_projection_e530"
    version = 1
    description = (
        "Random Gaussian projection (10 dims) of the concatenated static gene "
        "annotation vectors (gene_annotation, protein_annotation, gene_constraint)."
    )
    rationale = (
        "A low-dimensional random projection of the full static annotation matrix "
        "summarises high-dimensional annotation space into compact latent factors."
    )
    inputs = ["knowledge"]
    params = {"n_components": 10, "seed": 530}
    dim = 10

    def _build_gene_matrix(self, ctx):
        cache_key = "static_annotation_matrix_e530"
        if cache_key in ctx.cache:
            return ctx.cache[cache_key]

        genes = ctx.genes
        n = ctx.n_genes
        cols = []

        # --- gene_annotation ---
        ga = ctx.knowledge("gene_annotation")
        if ga and "genes" in ga:
            ga_cols = ga.get("columns", [])
            ga_genes = ga["genes"]
            # numeric columns only (skip amino-acid fraction block handled as numeric too)
            mat = np.full((n, len(ga_cols)), np.nan, dtype=np.float64)
            for gi, g in enumerate(genes):
                vals = ga_genes.get(g)
                if vals is None:
                    continue
                row = np.full(len(ga_cols), np.nan)
                for j, v in enumerate(vals):
                    if j >= len(ga_cols):
                        break
                    if v is None:
                        continue
                    try:
                        row[j] = float(v)
                    except (TypeError, ValueError):
                        pass
                mat[gi] = row
            cols.append(mat)

        # --- protein_annotation ---
        pa = ctx.knowledge("protein_annotation")
        if pa and "genes" in pa:
            pa_cols = pa.get("columns", [])
            pa_genes = pa["genes"]
            mat = np.full((n, len(pa_cols)), np.nan, dtype=np.float64)
            for gi, g in enumerate(genes):
                vals = pa_genes.get(g)
                if vals is None:
                    continue
                row = np.full(len(pa_cols), np.nan)
                for j, v in enumerate(vals):
                    if j >= len(pa_cols):
                        break
                    if v is None:
                        continue
                    try:
                        row[j] = float(v)
                    except (TypeError, ValueError):
                        pass
                mat[gi] = row
            cols.append(mat)

        # --- gene_constraint ---
        gc = ctx.knowledge("gene_constraint")
        if gc and "genes" in gc:
            gc_cols = gc.get("columns", [])
            gc_genes = gc["genes"]
            mat = np.full((n, len(gc_cols)), np.nan, dtype=np.float64)
            for gi, g in enumerate(genes):
                vals = gc_genes.get(g)
                if vals is None:
                    continue
                row = np.full(len(gc_cols), np.nan)
                for j, v in enumerate(vals):
                    if j >= len(gc_cols):
                        break
                    if v is None:
                        continue
                    try:
                        row[j] = float(v)
                    except (TypeError, ValueError):
                        pass
                mat[gi] = row
            cols.append(mat)

        if not cols:
            X = np.zeros((n, 1), dtype=np.float64)
        else:
            X = np.concatenate(cols, axis=1)

        # Clean: replace non-finite with column means (or 0 if all nan)
        with np.errstate(invalid="ignore"):
            col_mean = np.nanmean(X, axis=0)
        col_mean = np.where(np.isfinite(col_mean), col_mean, 0.0)
        inds = np.where(~np.isfinite(X))
        X[inds] = np.take(col_mean, inds[1])

        # Standardise columns
        col_std = X.std(axis=0)
        col_std = np.where(col_std > 1e-8, col_std, 1.0)
        X = (X - X.mean(axis=0)) / col_std

        ctx.cache[cache_key] = X
        return X

    def compute(self, ctx, perts, params):
        k = int(params.get("n_components", self.params["n_components"]))
        seed = int(params.get("seed", self.params["seed"]))
        X = self._build_gene_matrix(ctx)  # (n_genes, F)
        F = X.shape[1]

        rng = np.random.RandomState(seed)
        # fixed projection matrix (F, k) scaled 1/sqrt(F)
        W = rng.normal(0.0, 1.0, size=(F, k)) / np.sqrt(max(F, 1))
        proj = X.dot(W)  # (n_genes, k)

        out = np.zeros((len(perts), ctx.n_genes, self.dim), dtype=np.float64)
        for i in range(len(perts)):
            out[i] = proj[:, : self.dim]
        return out
