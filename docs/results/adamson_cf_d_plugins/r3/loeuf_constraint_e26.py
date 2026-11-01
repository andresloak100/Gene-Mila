import numpy as np
from genemila.features.api import Feature, register


@register
class LoeufConstraintE26(Feature):
    name = "loeuf_constraint_e26"
    version = 1
    description = "LOEUF score (oe_lof_upper) per gene from gnomAD gene constraint."
    rationale = ("Constraint reflects evolutionary pressure; genes under stronger constraint "
                 "may be more regulated in their responses to perturbations.")
    inputs = ["gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        knowledge = ctx.knowledge("gene_constraint")
        if knowledge is None:
            return out

        col_names = knowledge.get("columns", [])
        try:
            loeuf_idx = col_names.index("oe_lof_upper")
        except ValueError:
            return out

        genes_table = knowledge.get("genes", {}) or {}

        values = np.full(ctx.n_genes, np.nan, dtype=float)
        for g in ctx.genes:
            entry = genes_table.get(g)
            if entry is None:
                continue
            try:
                v = entry[loeuf_idx]
            except (IndexError, TypeError):
                continue
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv):
                values[ctx.gene_index[g]] = fv

        # Missing values: use median of observed values (finite), else 0.
        finite_mask = np.isfinite(values)
        if finite_mask.any():
            fill = float(np.median(values[finite_mask]))
        else:
            fill = 0.0
        values[~finite_mask] = fill

        out[:, :, 0] = values[None, :]
        return out
