import numpy as np
from genemila.features.api import Feature, register

@register
class AdditiveSqTimesPromoterCpG(Feature):
    name = "additive_sq_times_promoter_cpg_e400"
    version = 1
    description = "Elementwise product of additive_response_squared_e242 and cpg_oe_promoter from gene_annotation."
    rationale = "Multiplying additive_response_squared by promoter CpG observed/expected ratio captures nonlinear regulatory effects linked to CpG islands."
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        # cpg_oe_promoter per gene, default 0.0 when missing
        cpg = np.zeros(n, dtype=float)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes_ann = ann.get("genes", {})
            columns = ann.get("columns", [])
            idx = None
            for j, c in enumerate(columns):
                if c == "cpg_oe_promoter":
                    idx = j
                    break
            if idx is not None:
                for gi, g in enumerate(ctx.genes):
                    vals = genes_ann.get(g)
                    if vals is not None and idx < len(vals) and vals[idx] is not None:
                        cpg[gi] = float(vals[idx])
        # additive_response_squared_e242
        base = ctx.feature("additive_response_squared_e242", perts)
        # base shape (len(perts), n_genes, dim)
        out = np.asarray(base, dtype=float) * cpg[None, :, None]
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        if out.shape[-1] != 1:
            out = out[..., :1]
        return out
