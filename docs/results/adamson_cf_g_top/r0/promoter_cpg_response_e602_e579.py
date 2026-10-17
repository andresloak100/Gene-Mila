import numpy as np
from genemila.features.api import Feature, register


@register
class PromoterCpGResponse(Feature):
    name = "promoter_cpg_response_e602_e579"
    version = 1
    description = "Product of promoter CpG observed/expected ratio of gene g and mean_response of gene g."
    rationale = "CpG-rich promoters mark active chromatin; accessibility may scale a gene's responsiveness to perturbation."
    inputs = ["knowledge:gene_annotation", "train_delta"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        # cpg_oe_promoter is column index 11 in gene_annotation genes values
        cpg = np.zeros(n_genes, dtype=float)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes = ann.get("genes", {})
            col = 11
            for g, idx in ctx.gene_index.items():
                vals = genes.get(g)
                if vals is not None and len(vals) > col:
                    v = vals[col]
                    if v is not None:
                        try:
                            fv = float(v)
                            if np.isfinite(fv):
                                cpg[idx] = fv
                        except (TypeError, ValueError):
                            pass

        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            mean_resp = d.mean(axis=0)
            out[i, :, 0] = cpg * mean_resp
        return out
