import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGeneConstraintSimilarityE429(Feature):
    name = "target_gene_constraint_similarity_e429"
    version = 1
    description = "Cosine similarity between target gene's gnomAD constraint metrics and gene g's constraint metrics."
    rationale = "Genes with similar loss-of-function constraint profiles often function in the same essential pathways; perturbing one may affect the expression of the other."
    inputs = ["knowledge", "control_mean"]
    params = {"metric": "cosine"}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        kc = ctx.knowledge("gene_constraint")
        if kc is None:
            return out

        cols = kc.get("columns", [])
        genes_map = kc.get("genes", {})
        if not cols or not genes_map:
            return out

        # Collect numeric column indices (skip non-numeric / boolean-ish columns if any).
        # All listed constraint columns are numeric in gnomAD tables.
        n_cols = len(cols)
        feat_mat = np.full((n_genes, n_cols), np.nan, dtype=np.float64)

        gene_index = ctx.gene_index
        for g, vals in genes_map.items():
            j = gene_index.get(g)
            if j is None:
                continue
            if vals is None:
                continue
            for c in range(n_cols):
                v = vals[c] if c < len(vals) else None
                if v is None:
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv):
                    feat_mat[j, c] = fv

        # Replace NaN with column means (computed over measured genes), then zero-fill
        # columns that are entirely missing.
        col_means = np.nanmean(feat_mat, axis=0)
        col_means = np.where(np.isfinite(col_means), col_means, 0.0)
        nan_mask = ~np.isfinite(feat_mat)
        if nan_mask.any():
            feat_mat[nan_mask] = np.take(col_means, np.where(nan_mask)[1])

        # Standardise each column (z-score) so cosine reflects profile shape,
        # not scale differences between columns (LOEUF vs pLI vs counts).
        col_std = feat_mat.std(axis=0)
        col_std = np.where(col_std > 1e-12, col_std, 1.0)
        col_mean = feat_mat.mean(axis=0)
        z = (feat_mat - col_mean) / col_std

        # L2-normalise each gene vector
        norms = np.linalg.norm(z, axis=1)
        norms = np.where(norms > 1e-12, norms, 1.0)
        zn = z / norms[:, None]

        metric = params.get("metric", "cosine") if params else "cosine"

        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if not t_idx:
                continue
            t = t_idx[0]
            tv = zn[t]
            if metric == "cosine":
                sims = zn @ tv
            else:
                # fallback: cosine
                sims = zn @ tv
            out[i, :, 0] = sims

        return out
