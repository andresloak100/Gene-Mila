import numpy as np
from genemila.features.api import Feature, register

@register
class CpgOePromoterValueE57(Feature):
    name = "cpg_oe_promoter_value_e57"
    version = 1
    description = "Numeric feature: cpg_oe_promoter value for gene g."
    rationale = "High CpG promoters may be more transcriptionally responsive to perturbations."
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        ka = ctx.knowledge("gene_annotation")
        if ka is None:
            return out
        cols = ka.get("columns", [])
        try:
            ci = cols.index("cpg_oe_promoter")
        except ValueError:
            return out
        genes = ka.get("genes", {})
        vec = np.zeros(ctx.n_genes, dtype=float)
        for g, idx in ctx.gene_index.items():
            vals = genes.get(g)
            if vals is None:
                continue
            v = vals[ci] if ci < len(vals) else None
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv):
                vec[idx] = fv
        out[:, :, 0] = vec[None, :]
        return out
