import numpy as np
from genemila.features.api import Feature, register

@register
class RandomProjectionAllPriorsE226(Feature):
    name = "random_projection_all_priors_e226"
    version = 1
    description = "10-dim Gaussian random projection of concatenated gene annotation, protein annotation and constraint features."
    rationale = "Combining many weak prior-knowledge signals through a fixed random projection may reveal latent gene structure predictive of perturbation response without overfitting."
    inputs = ["knowledge"]
    params = {"n_components": 10, "seed": 226}
    dim = 10

    def _build_matrix(self, ctx, params):
        n_genes = ctx.n_genes
        gene_index = ctx.gene_index

        cols = []
        # gene_annotation
        ga = ctx.knowledge("gene_annotation")
        if ga and isinstance(ga, dict) and "genes" in ga:
            gene_cols = ga.get("columns", [])
            units = ga.get("column_units", {})
            # numeric columns only: those with units not None/string? We'll attempt to parse all as float.
            genes_map = ga["genes"]
            # Determine number of columns from first entry
            sample = None
            for k, v in genes_map.items():
                if v is not None:
                    sample = v
                    break
            if sample is not None:
                ncol = len(sample)
                mat = np.full((n_genes, ncol), np.nan, dtype=float)
                for g, vals in genes_map.items():
                    gi = gene_index.get(g)
                    if gi is None or vals is None:
                        continue
                    for j in range(min(ncol, len(vals))):
                        val = vals[j]
                        if val is None:
                            continue
                        try:
                            mat[gi, j] = float(val)
                        except (TypeError, ValueError):
                            pass
                cols.append(mat)

        # protein_annotation
        pa = ctx.knowledge("protein_annotation")
        if pa and isinstance(pa, dict) and "genes" in pa:
            genes_map = pa["genes"]
            sample = None
            for k, v in genes_map.items():
                if v is not None:
                    sample = v
                    break
            if sample is not None:
                ncol = len(sample)
                mat = np.full((n_genes, ncol), np.nan, dtype=float)
                for g, vals in genes_map.items():
                    gi = gene_index.get(g)
                    if gi is None or vals is None:
                        continue
                    for j in range(min(ncol, len(vals))):
                        val = vals[j]
                        if val is None:
                            continue
                        try:
                            mat[gi, j] = float(val)
                        except (TypeError, ValueError):
                            pass
                cols.append(mat)

        # gene_constraint
        gc = ctx.knowledge("gene_constraint")
        if gc and isinstance(gc, dict) and "genes" in gc:
            genes_map = gc["genes"]
            sample = None
            for k, v in genes_map.items():
                if v is not None:
                    sample = v
                    break
            if sample is not None:
                ncol = len(sample)
                mat = np.full((n_genes, ncol), np.nan, dtype=float)
                for g, vals in genes_map.items():
                    gi = gene_index.get(g)
                    if gi is None or vals is None:
                        continue
                    for j in range(min(ncol, len(vals))):
                        val = vals[j]
                        if val is None:
                            continue
                        try:
                            mat[gi, j] = float(val)
                        except (TypeError, ValueError):
                            pass
                cols.append(mat)

        if not cols:
            return np.zeros((n_genes, 1), dtype=float)

        X = np.concatenate(cols, axis=1)
        # median fill per column
        med = np.nanmedian(X, axis=0)
        med = np.where(np.isnan(med), 0.0, med)
        inds = np.where(np.isnan(X))
        if len(inds[0]) > 0:
            X[inds] = np.take(med, inds[1])
        # standardize
        mu = X.mean(axis=0)
        sd = X.std(axis=0)
        sd = np.where(sd < 1e-12, 1.0, sd)
        X = (X - mu) / sd
        return X

    def compute(self, ctx, perts, params):
        n_comp = int(params.get("n_components", 10))
        seed = int(params.get("seed", 226))
        key = ("rp_all_priors", n_comp, seed)
        cache = ctx.cache
        if key not in cache:
            X = self._build_matrix(ctx, params)
            n_genes, n_feat = X.shape
            rng = np.random.RandomState(seed)
            if n_feat == 0:
                proj = np.zeros((n_genes, n_comp), dtype=float)
            else:
                W = rng.randn(n_feat, n_comp) / np.sqrt(max(n_feat, 1))
                proj = X @ W
            cache[key] = proj.astype(float)
        proj = cache[key]
        out = np.zeros((len(perts), ctx.n_genes, n_comp), dtype=float)
        for i in range(len(perts)):
            out[i] = proj
        return out
