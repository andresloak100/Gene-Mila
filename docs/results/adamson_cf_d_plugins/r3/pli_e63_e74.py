import numpy as np
from genemila.features.api import Feature, register


@register
class PLI_e63_e74(Feature):
    name = "pli_e63_e74"
    version = 1
    description = "Probability of loss-of-function intolerance (pLI) for gene g from gene_constraint."
    rationale = ("LoF-intolerant genes are under stronger selection and may have more robust "
                 "expression regulation, reducing response magnitude.")
    inputs = ["gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        pli = np.zeros(n_genes, dtype=float)

        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            genes_tbl = kc.get("genes", {}) or {}
            columns = kc.get("columns", []) or []
            # locate pLI column index (case-insensitive)
            pli_idx = None
            for j, c in enumerate(columns):
                if str(c).lower() == "pli":
                    pli_idx = j
                    break
            if pli_idx is not None:
                for gi, g in enumerate(ctx.genes):
                    vals = genes_tbl.get(g)
                    if vals is None:
                        continue
                    try:
                        v = vals[pli_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        pli[gi] = fv

        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = pli[np.newaxis, :]
        return out
