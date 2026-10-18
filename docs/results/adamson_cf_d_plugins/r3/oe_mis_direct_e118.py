import numpy as np
from genemila.features.api import Feature, register


@register
class OeMisDirectE118(Feature):
    name = "oe_mis_direct_e118"
    version = 1
    description = "Numeric feature: oe_mis value from gene_constraint for gene g."
    rationale = ("Missense constraint reflects functional importance; highly constrained "
                 "genes may be buffered expression, so lower oe_mis (more constrained) "
                 "may associate with smaller perturbation responses.")
    inputs = ["gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        kc = ctx.knowledge("gene_constraint")
        if kc is None:
            return out

        genes_table = kc.get("genes", {}) or {}
        columns = kc.get("columns", []) or []
        try:
            col_idx = columns.index("oe_mis")
        except ValueError:
            return out

        # Build per-gene oe_mis vector aligned with ctx.genes
        vec = np.full(ctx.n_genes, np.nan, dtype=float)
        for gi, sym in enumerate(ctx.genes):
            vals = genes_table.get(sym)
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

        # Fill missing with column mean (finite fallback), else 0
        finite_mask = np.isfinite(vec)
        if finite_mask.any():
            fill = float(vec[finite_mask].mean())
        else:
            fill = 0.0
        vec = np.where(finite_mask, vec, fill)

        out[:, :, 0] = vec[None, :]
        return out
