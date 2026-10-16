import numpy as np
from genemila.features.api import Feature, register

@register
class TargetPromoterCpG(Feature):
    name = "target_promoter_cpg_e406"
    version = 1
    description = "Mean promoter CpG observed/expected ratio of the perturbation's target gene(s)."
    rationale = "Promoter CpG content is associated with gene regulation and may influence CRISPRa efficiency or downstream effects."
    inputs = ["knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))
        ann = ctx.knowledge("gene_annotation")
        if not ann:
            return out
        genes = ann.get("genes", {})
        columns = ann.get("columns", [])
        try:
            cpg_idx = columns.index("cpg_oe_promoter")
        except ValueError:
            return out
        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            vals = []
            for t in targets:
                row = genes.get(t)
                if row is None:
                    continue
                v = row[cpg_idx]
                if v is not None:
                    vals.append(float(v))
            if vals:
                out[i, :, 0] = np.mean(vals)
        return out
