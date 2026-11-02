import numpy as np
from genemila.features.api import Feature, register


@register
class LoeufE44(Feature):
    name = "loeuf_e44"
    version = 1
    description = "LOEUF (oe_lof_upper) per gene from gnomAD gene constraint."
    rationale = (
        "LoF-intolerant genes (low LOEUF) may be more tightly regulated and respond "
        "more strongly to perturbations; encodes per-gene LoF constraint as a covariate."
    )
    inputs = ["gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        kc = ctx.knowledge("gene_constraint")
        if not kc:
            return out

        genes_tbl = kc.get("genes", {}) or {}
        columns = kc.get("columns", []) or []
        try:
            col_idx = list(columns).index("oe_lof_upper")
        except ValueError:
            return out

        # Build per-column LOEUF vector aligned to ctx.genes; missing/None -> 0.
        vals = np.zeros(n_genes, dtype=float)
        for gi, g in enumerate(ctx.genes):
            row = genes_tbl.get(g)
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
                vals[gi] = fv

        out[:, :, 0] = vals[None, :]
        return out
