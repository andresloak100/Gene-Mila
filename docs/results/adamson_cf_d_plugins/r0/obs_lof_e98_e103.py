import numpy as np
from genemila.features.api import Feature, register


@register
class ObsLofE98E103(Feature):
    name = "obs_lof_e98_e103"
    version = 1
    description = "Number of observed loss-of-function variants for gene g from gene_constraint."
    rationale = ("Genes with many observed LoF variants are less essential and may have "
                 "less buffering, leading to larger expression changes when perturbed.")
    inputs = ["gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        knowledge = ctx.knowledge("gene_constraint")
        if knowledge is None:
            return out

        genes_table = knowledge.get("genes", {})
        columns = knowledge.get("columns", [])
        try:
            col_idx = columns.index("obs_lof")
        except ValueError:
            return out

        # Build a per-gene value vector aligned to ctx.genes
        values = np.full(ctx.n_genes, np.nan, dtype=float)
        for g, gidx in ctx.gene_index.items():
            row = genes_table.get(g)
            if row is None:
                continue
            try:
                v = row[col_idx]
            except (IndexError, TypeError):
                continue
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv):
                values[gidx] = fv

        # Missing values -> 0 (no observed LoF variants)
        values = np.where(np.isfinite(values), values, 0.0)

        # Same value for every perturbation row (gene-level property)
        out[:, :, 0] = values[None, :]
        return out
