import numpy as np
from genemila.features.api import Feature, register


@register
class GeneConstraintOeLofUpperBinE145(Feature):
    name = "gene_constraint_oe_lof_upper_bin_e145"
    version = 1
    description = "Ordinal encoding of the oe_lof_upper_bin column from gene_constraint for gene g."
    rationale = ("LoF-intolerant genes (low LOEUF bin) are under stronger purifying selection "
                 "and may have more buffered expression, affecting their response to perturbations.")
    inputs = ["knowledge:gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        kc = ctx.knowledge("gene_constraint")
        if not kc:
            return out

        columns = kc.get("columns", [])
        genes_tbl = kc.get("genes", {}) or {}

        try:
            bin_idx = columns.index("oe_lof_upper_bin")
        except (ValueError, AttributeError):
            return out

        # Build gene -> ordinal bin value mapping.
        gene_val = {}
        for g, vals in genes_tbl.items():
            if vals is None:
                continue
            try:
                v = vals[bin_idx]
            except (IndexError, TypeError):
                continue
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if not np.isfinite(fv):
                continue
            gene_val[g] = fv

        if not gene_val:
            return out

        # Vectorise: fill per-gene column once.
        col = np.zeros(ctx.n_genes, dtype=float)
        for g, v in gene_val.items():
            j = ctx.gene_index.get(g)
            if j is not None:
                col[j] = v

        out[:, :, 0] = col[None, :]
        return out
