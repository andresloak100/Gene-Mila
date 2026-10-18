import numpy as np
from genemila.features.api import Feature, register

@register
class OeMisE96E101(Feature):
    name = "oe_mis_e96_e101"
    version = 1
    description = "Observed/expected missense ratio (oe_mis) per gene from gnomAD constraint."
    rationale = ("Low oe_mis indicates strong purifying selection on missense variants, "
                 "implying tighter regulatory control and potentially larger expression "
                 "changes upon perturbation.")
    inputs = ["gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.full((len(perts), n_genes, 1), np.nan, dtype=float)

        kc = ctx.knowledge("gene_constraint")
        col = np.full(n_genes, np.nan, dtype=float)

        if kc is not None and isinstance(kc, dict):
            columns = kc.get("columns", [])
            genes = kc.get("genes", {})
            try:
                idx = columns.index("oe_mis")
            except (ValueError, AttributeError):
                idx = None
            if idx is not None and isinstance(genes, dict):
                for g, vals in genes.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None or vals is None:
                        continue
                    try:
                        v = vals[idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        col[gi] = fv

        # Fill missing with the mean of observed values (or 0 if none)
        finite_mask = np.isfinite(col)
        if finite_mask.any():
            fill = float(col[finite_mask].mean())
        else:
            fill = 0.0
        col = np.where(finite_mask, col, fill)

        out[:, :, 0] = col[None, :]
        return out
