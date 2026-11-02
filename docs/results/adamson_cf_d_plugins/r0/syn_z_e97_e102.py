import numpy as np
from genemila.features.api import Feature, register


@register
class SynZScore(Feature):
    name = "syn_z_e97_e102"
    version = 1
    description = "Synonymous constraint Z-score for gene g from gene_constraint."
    rationale = (
        "High synonymous constraint indicates selection on mRNA-level features, "
        "which may stabilize expression and reduce perturbation response."
    )
    inputs = ["gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))

        table = ctx.knowledge("gene_constraint")
        col_idx = None
        genes_table = None
        if table is not None:
            cols = table.get("columns", [])
            if "syn_z" in cols:
                col_idx = cols.index("syn_z")
            genes_table = table.get("genes", None)

        if col_idx is None or genes_table is None:
            return out

        # Build a per-gene vector aligned to ctx.genes
        vec = np.full(ctx.n_genes, np.nan, dtype=float)
        for g, col in ctx.gene_index.items():
            vals = genes_table.get(g)
            if vals is None:
                continue
            try:
                v = vals[col_idx]
            except (IndexError, TypeError):
                continue
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv):
                vec[col] = fv

        # Fill missing with 0 (neutral)
        vec = np.where(np.isfinite(vec), vec, 0.0)

        out[:, :, 0] = vec[None, :]
        return out
