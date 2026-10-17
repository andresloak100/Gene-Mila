import numpy as np
from genemila.features.api import Feature, register


@register
class RandomProjectionStaticFeatures(Feature):
    name = "random_projection_static_features_e410"
    version = 1
    description = ("Random projection of concatenated static gene and target features "
                   "(annotation, protein, constraint) into a scalar per (p, g).")
    rationale = ("A fixed random projection of many weak static features acts as a "
                 "regularized low-dimensional summary, capturing latent structure.")
    inputs = ["knowledge", "target_genes"]
    params = {"seed": 42, "n_components": 1}
    dim = 1

    def _build_gene_matrix(self, ctx):
        # Cached per-context construction of static gene feature matrix.
        cache = ctx.cache
        key = "rp_static_e410_matrix"
        if key in cache:
            return cache[key]

        n_genes = ctx.n_genes
        gene_index = ctx.gene_index

        # --- gene_annotation ---
        ga = ctx.knowledge("gene_annotation")
        ga_cols = []
        if ga is not None and isinstance(ga, dict) and "genes" in ga:
            cols = ga.get("columns", [])
            # numeric columns only (first block before aa_*)
            num_cols = []
            for c in cols:
                if isinstance(c, str) and c.startswith("aa_"):
                    break
                num_cols.append(c)
            ga_genes = ga["genes"]
            mat = np.zeros((n_genes, len(num_cols)), dtype=np.float64)
            for g, gi in gene_index.items():
                vals = ga_genes.get(g)
                if vals is None:
                    continue
                for j in range(len(num_cols)):
                    if j < len(vals):
                        v = vals[j]
                        if v is not None:
                            try:
                                fv = float(v)
                                if np.isfinite(fv):
                                    mat[gi, j] = fv
                            except (TypeError, ValueError):
                                pass
            ga_cols.append(mat)

        # --- protein_annotation ---
        pa = ctx.knowledge("protein_annotation")
        if pa is not None and isinstance(pa, dict) and "genes" in pa:
            cols = pa.get("columns", [])
            pa_genes = pa["genes"]
            mat = np.zeros((n_genes, len(cols)), dtype=np.float64)
            for g, gi in gene_index.items():
                vals = pa_genes.get(g)
                if vals is None:
                    continue
                for j in range(len(cols)):
                    if j < len(vals):
                        v = vals[j]
                        if v is not None:
                            try:
                                fv = float(v)
                                if np.isfinite(fv):
                                    mat[gi, j] = fv
                            except (TypeError, ValueError):
                                pass
            ga_cols.append(mat)

        # --- gene_constraint ---
        gc = ctx.knowledge("gene_constraint")
        if gc is not None and isinstance(gc, dict) and "genes" in gc:
            cols = gc.get("columns", [])
            gc_genes = gc["genes"]
            mat = np.zeros((n_genes, len(cols)), dtype=np.float64)
            for g, gi in gene_index.items():
                vals = gc_genes.get(g)
                if vals is None:
                    continue
                for j in range(len(cols)):
                    if j < len(vals):
                        v = vals[j]
                        if v is not None:
                            try:
                                fv = float(v)
                                if np.isfinite(fv):
                                    mat[gi, j] = fv
                            except (TypeError, ValueError):
                                pass
            ga_cols.append(mat)

        if ga_cols:
            G = np.concatenate(ga_cols, axis=1)
        else:
            G = np.zeros((n_genes, 1), dtype=np.float64)

        # Standardize columns (guard zero std)
        mu = G.mean(axis=0)
        sd = G.std(axis=0)
        sd = np.where(sd > 1e-8, sd, 1.0)
        G = (G - mu) / sd

        cache[key] = G
        return G

    def _target_vector(self, ctx, p):
        # Static features for the target gene(s) of p: mean of gene rows.
        G = self._build_gene_matrix(ctx)
        tgt_idx = ctx.target_indices(p)
        if not tgt_idx:
            return np.zeros(G.shape[1], dtype=np.float64)
        return G[np.asarray(tgt_idx, dtype=int)].mean(axis=0)

    def compute(self, ctx, perts, params):
        seed = int(params.get("seed", 42))
        n_components = int(params.get("n_components", 1))
        G = self._build_gene_matrix(ctx)
        d = G.shape[1]

        # Fixed random projection (only first component used for dim=1)
        rng = np.random.RandomState(seed)
        W = rng.randn(d, max(n_components, 1))
        w = W[:, 0]

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=np.float64)
        for i, p in enumerate(perts):
            tv = self._target_vector(ctx, p)
            # concatenate [gene features, target features] then project
            # equivalent to gene_part + target_part (additive)
            gene_part = G @ w
            target_part = float(tv @ w)
            out[i, :, 0] = gene_part + target_part

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
