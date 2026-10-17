import numpy as np
from genemila.features.api import Feature, register


@register
class ProteinAnnotationRandomProjection(Feature):
    name = "protein_annotation_random_projection_e668"
    version = 1
    description = "Random projection of protein_annotation numeric features for the perturbation's target gene(s)."
    rationale = ("Protein annotation features are high-dimensional and may contain latent nonlinear structure; "
                 "a fixed random projection captures combinations not represented by individual columns.")
    inputs = ["knowledge", "target_genes"]
    params = {"n_components": 5, "seed": 42}
    dim = 5

    def compute(self, ctx, perts, params):
        k = int(params.get("n_components", 5))
        seed = int(params.get("seed", 42))
        n_genes = ctx.n_genes

        cache = ctx.cache
        key = ("prot_rp", k, seed, n_genes)
        proj = cache.get(key)

        if proj is None:
            proj = np.zeros((n_genes, k), dtype=float)
            ann = ctx.knowledge("protein_annotation")
            if ann is not None:
                cols = ann.get("columns", [])
                genes_dict = ann.get("genes", {}) or {}
                # Determine which columns are numeric (exclude any non-numeric-like names)
                num_cols = [c for c in cols if not isinstance(c, str) or not c.startswith("aa_")]
                # Build matrix over genes present in annotation
                syms = list(genes_dict.keys())
                mat = np.full((len(syms), len(num_cols)), np.nan, dtype=float)
                for i, s in enumerate(syms):
                    vals = genes_dict[s]
                    for j, c in enumerate(num_cols):
                        idx = cols.index(c)
                        v = vals[idx] if idx < len(vals) else None
                        if v is None:
                            mat[i, j] = np.nan
                        else:
                            try:
                                mat[i, j] = float(v)
                            except (TypeError, ValueError):
                                mat[i, j] = np.nan
                # Impute nan with column means (or 0 if all nan)
                if mat.shape[0] > 0 and mat.shape[1] > 0:
                    col_mean = np.nanmean(mat, axis=0)
                    col_mean = np.where(np.isfinite(col_mean), col_mean, 0.0)
                    inds = np.where(~np.isfinite(mat))
                    mat[inds] = np.take(col_mean, inds[1])
                    # Standardize columns
                    mu = mat.mean(axis=0)
                    sd = mat.std(axis=0)
                    sd = np.where(sd > 1e-12, sd, 1.0)
                    mat = (mat - mu) / sd
                    n_comp = min(k, mat.shape[1], mat.shape[0])
                    if n_comp >= 1:
                        from sklearn.random_projection import GaussianRandomProjection
                        rp = GaussianRandomProjection(n_components=n_comp, random_state=seed)
                        emb = rp.fit_transform(mat)
                        # Map back to gene columns
                        for i, s in enumerate(syms):
                            gi = ctx.gene_index.get(s)
                            if gi is not None:
                                proj[gi, :n_comp] = emb[i]
            cache[key] = proj

        out = np.zeros((len(perts), n_genes, k), dtype=float)
        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            idxs = [ctx.gene_index[g] for g in tgenes if g in ctx.gene_index]
            if idxs:
                vec = proj[idxs, :].mean(axis=0)
            else:
                vec = np.zeros(k, dtype=float)
            out[i, :, :] = vec[None, :]
        return out
