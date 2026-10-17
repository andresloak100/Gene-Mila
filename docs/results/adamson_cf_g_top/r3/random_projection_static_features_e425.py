import numpy as np
from genemila.features.api import Feature, register


@register
class RandomProjectionStaticFeatures(Feature):
    name = "random_projection_static_features_e425"
    version = 1
    description = ("Concatenate static gene features (annotation, constraint, protein) for the "
                   "gene and the perturbation target, project with a fixed random matrix to "
                   "n_components dims.")
    rationale = ("A fixed random projection of static per-gene descriptors may capture latent "
                 "structure predictive of the response without using any response labels.")
    inputs = ["knowledge"]
    params = {"n_components": 20, "seed": 42}
    dim = 20

    def _build_gene_matrix(self, ctx, params):
        cache = ctx.cache
        key = ("rp_static", params.get("seed", 42))
        if key in cache:
            return cache[key]

        n_genes = ctx.n_genes
        gene_index = ctx.gene_index
        cols = []

        def add_table(name, prefixes):
            data = ctx.knowledge(name)
            if not data:
                return
            genes = data.get("genes", {}) or {}
            columns = data.get("columns", []) or []
            # Determine numeric columns. We'll just try to parse floats per gene.
            for ci, cname in enumerate(columns):
                if not isinstance(cname, str):
                    continue
                # skip aa_* amino acid fractions? keep them (they are static, numeric)
                vec = np.zeros(n_genes, dtype=np.float64)
                for g, gi in gene_index.items():
                    vals = genes.get(g)
                    if vals is None:
                        continue
                    try:
                        v = vals[ci]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        vec[gi] = float(v)
                    except (TypeError, ValueError):
                        continue
                cols.append(vec)

        add_table("gene_annotation", None)
        add_table("gene_constraint", None)
        add_table("protein_annotation", None)

        if not cols:
            # fallback: use control mean/std as static features (still no response labels)
            cols = [ctx.control_mean.astype(np.float64),
                    ctx.control_std.astype(np.float64)]

        M = np.stack(cols, axis=1)  # (n_genes, n_features)
        # standardize each column (handle constants)
        mu = M.mean(axis=0)
        sd = M.std(axis=0)
        sd = np.where(sd > 1e-12, sd, 1.0)
        M = (M - mu) / sd
        M = np.nan_to_num(M, nan=0.0, posinf=0.0, neginf=0.0)
        cache[key] = M
        return M

    def compute(self, ctx, perts, params):
        n_components = int(params.get("n_components", 20))
        seed = int(params.get("seed", 42))
        M = self._build_gene_matrix(ctx, params)  # (n_genes, F)
        F = M.shape[1]
        rng = np.random.RandomState(seed)
        # projection matrix for gene features: F -> n_components
        R_gene = rng.randn(F, n_components) / np.sqrt(max(F, 1))
        # projection for target features (same F) into same space
        R_tgt = rng.randn(F, n_components) / np.sqrt(max(F, 1))

        gene_proj = M @ R_gene  # (n_genes, n_components)

        out = np.zeros((len(perts), ctx.n_genes, n_components), dtype=np.float64)
        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if tgt_idx:
                tgt_vec = M[tgt_idx].mean(axis=0)  # (F,)
            else:
                tgt_vec = np.zeros(F, dtype=np.float64)
            tgt_proj = tgt_vec @ R_tgt  # (n_components,)
            out[i] = gene_proj + tgt_proj[None, :]

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
