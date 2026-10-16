import numpy as np
from genemila.features.api import Feature, register

@register
class CpgOePromoterXAdditiveE129(Feature):
    name = "cpg_oe_promoter_x_additive_e129"
    version = 1
    description = "Product of cpg_oe_promoter of gene g and additive_response."
    rationale = "CpG island promoter status modulates CRISPRa response; interaction with additive response captures this."
    inputs = ["control_cells", "gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1))

        # Load cpg_oe_promoter per gene from gene_annotation
        cpg = np.full(n, np.nan)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes_map = ann.get("genes", {})
            cols = ann.get("columns", [])
            try:
                idx = cols.index("cpg_oe_promoter")
            except ValueError:
                idx = None
            if idx is not None:
                for gi, g in enumerate(ctx.genes):
                    vals = genes_map.get(g)
                    if vals is not None and idx < len(vals) and vals[idx] is not None:
                        cpg[gi] = float(vals[idx])
        cpg = np.where(np.isfinite(cpg), cpg, 0.0)

        # Precompute leave-one-out mean deltas for all genes, per perturbation
        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            add = np.zeros(n)
            if len(tg) > 0:
                _, d = ctx.train_delta(exclude=p)
                # mean over training rows for each gene column
                col_mean = d.mean(axis=0)  # shape (n_genes,)
                for t in tg:
                    ti = ctx.gene_index.get(t)
                    if ti is None:
                        continue
                    add += col_mean[ti]
            out[i, :, 0] = cpg * add
        return out
