import numpy as np
from genemila.features.api import Feature, register

@register
class GeneLoeufE254(Feature):
    name = "gene_loeuf_e254"
    version = 1
    description = "LOEUF (oe_lof_upper) of gene g, median-filled."
    rationale = "Genes under high LoF constraint (low LOEUF) may have tighter regulation and dampened response magnitude."
    inputs = ["knowledge:gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        vals = np.full(n_genes, np.nan, dtype=float)

        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            cols = kc.get("columns", [])
            genes_map = kc.get("genes", {}) or {}
            try:
                idx = cols.index("oe_lof_upper")
            except ValueError:
                idx = None
            if idx is not None:
                for gi, g in enumerate(ctx.genes):
                    row = genes_map.get(g)
                    if row is None:
                        continue
                    try:
                        v = row[idx]
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

        finite = vals[np.isfinite(vals)]
        if finite.size > 0:
            med = float(np.median(finite))
        else:
            med = 0.0
        vals = np.where(np.isfinite(vals), vals, med)

        out = np.empty((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = vals[None, :]
        return out
