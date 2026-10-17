import numpy as np
from genemila.features.api import Feature, register


@register
class StaticAnnotationRandomProjectionE518(Feature):
    name = "static_annotation_random_projection_e518"
    version = 1
    description = ("10-dim Gaussian random projection of each gene's static annotation "
                   "vector (gene_annotation + protein_annotation + gene_constraint).")
    rationale = ("A compressed low-dimensional representation of static annotation may capture "
                 "latent structure relevant to perturbation response that individual features miss.")
    inputs = ["knowledge"]
    params = {"n_components": 10}
    dim = 10

    def _knowledge_matrix(self, ctx, name):
        kn = ctx.knowledge(name)
        if not kn or "genes" not in kn:
            return None
        gmap = kn["genes"]
        genes = ctx.genes
        n = len(genes)
        ncols = None
        for g in genes:
            v = gmap.get(g)
            if v is not None:
                ncols = len(v)
                break
        if not ncols:
            return None
        mat = np.full((n, ncols), np.nan, dtype=np.float64)
        for i, g in enumerate(genes):
            v = gmap.get(g)
            if v is None:
                continue
            for j in range(min(ncols, len(v))):
                x = v[j]
                if x is None:
                    continue
                try:
                    mat[i, j] = float(x)
                except (TypeError, ValueError):
                    pass
        return mat

    def _build_matrix(self, ctx, n_comp):
        key = ("_sarp_matrix", n_comp)
        cache = ctx.cache
        if key in cache:
            return cache[key]

        cols = []
        for name in ("gene_annotation", "protein_annotation", "gene_constraint"):
            m = self._knowledge_matrix(ctx, name)
            if m is not None:
                cols.append(m)

        if not cols:
            X = np.column_stack([ctx.control_mean, ctx.control_std])
        else:
            X = np.hstack(cols)

        with np.errstate(invalid="ignore"):
            colmean = np.nanmean(X, axis=0)
        colmean = np.where(np.isfinite(colmean), colmean, 0.0)
        inds = np.where(~np.isfinite(X))
        if inds[0].size:
            X[inds] = colmean[inds[1]]

        mu = X.mean(axis=0)
        sd = X.std(axis=0)
        sd = np.where(sd > 1e-12, sd, 1.0)
        X = (X - mu) / sd

        d = X.shape[1]
        k = int(min(n_comp, d)) if d > 0 else 0
        if k > 0:
            rng = np.random.RandomState(0)
            R = rng.randn(d, k) / np.sqrt(k)
            P = X @ R
        else:
            P = np.zeros((X.shape[0], 0), dtype=np.float64)

        if P.shape[1] < n_comp:
            P = np.hstack([P, np.zeros((P.shape[0], n_comp - P.shape[1]))])
        P = P[:, :n_comp].astype(np.float64)
        P = np.nan_to_num(P, nan=0.0, posinf=0.0, neginf=0.0)

        cache[key] = P
        return P

    def compute(self, ctx, perts, params):
        n_comp = int(params.get("n_components", self.params["n_components"]))
        P = self._build_matrix(ctx, n_comp)
        out = np.empty((len(perts), ctx.n_genes, n_comp), dtype=np.float64)
        for i in range(len(perts)):
            out[i] = P
        return out
