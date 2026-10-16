import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveTimesCpgOePromoterSquared(Feature):
    name = "additive_times_cpg_oe_promoter_squared_e473"
    version = 1
    description = "Elementwise product of additive_response and squared cpg_oe_promoter of gene g."
    rationale = ("Nonlinear effect of CpG observed/expected ratio may capture promoter "
                 "methylation influence; squaring emphasizes extremes.")
    inputs = ["control_cells"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1))

        # additive_response feature
        add = ctx.feature("additive_response", perts)
        if add.ndim == 3:
            add = add[:, :, 0]

        # cpg_oe_promoter from gene_annotation knowledge
        cpg = np.zeros(ctx.n_genes)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes_data = ann.get("genes", {})
            columns = ann.get("columns", [])
            try:
                idx = columns.index("cpg_oe_promoter")
            except ValueError:
                idx = None
            if idx is not None:
                for g, gi in ctx.gene_index.items():
                    vals = genes_data.get(g)
                    if vals is not None and idx < len(vals) and vals[idx] is not None:
                        cpg[gi] = float(vals[idx])

        cpg_sq = cpg * cpg
        out[:, :, 0] = add * cpg_sq[None, :]
        return out
