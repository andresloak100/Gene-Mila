import numpy as np
from genemila.features.api import Feature, register


@register
class GeneAnnotationRandomProjection(Feature):
    name = "gene_annotation_random_projection_e717"
    version = 1
    description = ("Random Gaussian projection of standardized per-gene annotation "
                   "features (GENCODE/UniProt-derived numeric columns) to k dimensions.")
    rationale = ("Gene annotation carries many correlated numeric properties; a fixed "
                 "random projection summarizes them into a low-dimensional latent "
                 "signature per gene without overfitting, potentially capturing genomic "
                 "properties that modulate perturbation response.")
    inputs = ["knowledge"]
    params = {"k": 10}
    dim = 10

    def compute(self, ctx, perts, params):
        k = int(params.get("k", 10))
        if k <= 0:
            k = 1

        n_genes = ctx.n_genes
        gene_index = ctx.gene_index

        # Build a per-gene numeric annotation matrix from available knowledge tables.
        cache = ctx.cache
        key = "_gare717_matrix"
        if key in cache:
            mat = cache[key]
        else:
            mat = self._build_matrix(ctx)
            cache[key] = mat

        # mat: (n_genes, n_feats) with NaNs for missing
        n_feats = mat.shape[1] if mat is not None else 0

        # Fixed random projection matrix (seeded for reproducibility).
        rng = np.random.RandomState(717)
        if n_feats > 0:
            proj = rng.normal(size=(n_feats, k)) / np.sqrt(max(n_feats, 1))
        else:
            proj = None

        # Standardize features using finite entries only.
        if n_feats > 0:
            filled = mat.copy()
            col_mean = np.nanmean(filled, axis=0)
            col_std = np.nanstd(filled, axis=0)
            col_std[~np.isfinite(col_std) | (col_std < 1e-8)] = 1.0
            col_mean[~np.isfinite(col_mean)] = 0.0
            nan_mask = ~np.isfinite(filled)
            filled[nan_mask] = 0.0
            z = (filled - col_mean) / col_std
            z[nan_mask] = 0.0
            proj_vals = z @ proj  # (n_genes, k)
        else:
            proj_vals = np.zeros((n_genes, k))

        # Ensure finite.
        proj_vals = np.nan_to_num(proj_vals, nan=0.0, posinf=0.0, neginf=0.0)

        # Same per-gene vector for every perturbation row.
        out = np.zeros((len(perts), n_genes, k))
        out[:] = proj_vals[np.newaxis, :, :]
        return out

    def _build_matrix(self, ctx):
        n_genes = ctx.n_genes
        gene_index = ctx.gene_index
        columns = []

        def add_table(name, skip_flags=True):
            table = ctx.knowledge(name)
            if not isinstance(table, dict):
                return
            genes = table.get("genes")
            cols = table.get("columns")
            if not isinstance(genes, dict) or not isinstance(cols, list):
                return
            for ci, colname in enumerate(cols):
                if skip_flags and "flag" in str(colname).lower():
                    continue
                vec = np.full(n_genes, np.nan, dtype=float)
                any_val = False
                for sym, vals in genes.items():
                    gi = gene_index.get(sym)
                    if gi is None:
                        continue
                    try:
                        v = vals[ci]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        vec[gi] = fv
                        any_val = True
                if any_val:
                    columns.append(vec)

        add_table("gene_annotation")
        add_table("gene_constraint")
        add_table("protein_annotation")

        if not columns:
            return None
        return np.vstack(columns).T  # (n_genes, n_feats)
