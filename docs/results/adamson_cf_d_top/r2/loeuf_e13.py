import numpy as np
from genemila.features.api import Feature, register


@register
class LoeufE13(Feature):
    name = "loeuf_e13"
    version = 1
    description = "LOEUF (oe_lof_upper) from gnomAD gene_constraint, as a gene-side feature."
    rationale = ("LoF-intolerant genes are under stronger selective pressure and may have more "
                 "stable expression, reducing their perturbation response magnitude.")
    inputs = ["gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        table = ctx.knowledge("gene_constraint")
        if table is None:
            return out

        genes = table.get("genes", {}) or {}
        columns = table.get("columns", []) or []
        try:
            col_idx = list(columns).index("oe_lof_upper")
        except ValueError:
            return out

        # Build gene -> LOEUF vector aligned to ctx.genes
        vec = np.full(ctx.n_genes, np.nan, dtype=float)
        for gi, g in enumerate(ctx.genes):
            vals = genes.get(g)
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
                vec[gi] = fv

        # Impute missing with mean of observed (finite) values; fallback 0
        finite = np.isfinite(vec)
        if finite.any():
            fill = float(np.mean(vec[finite]))
        else:
            fill = 0.0
        vec[~finite] = fill

        out[:, :, 0] = vec[None, :]
        return out
