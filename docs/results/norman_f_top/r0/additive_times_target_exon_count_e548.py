import numpy as np
from genemila.features.api import Feature, register

@register
class AdditiveTimesTargetExonCountE548(Feature):
    name = "additive_times_target_exon_count_e548"
    version = 1
    description = "Elementwise product of additive_response and the sum of n_exons over all targets of p."
    rationale = "Exon count may influence CRISPRa efficiency or downstream effects; interaction with additive response could be informative."
    inputs = ["gene_annotation", "additive_response"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))

        ann = ctx.knowledge("gene_annotation")
        if ann is None:
            return out
        genes_ann = ann.get("genes", {})
        cols = ann.get("columns", [])
        if "n_exons" not in cols:
            return out
        exon_idx = cols.index("n_exons")

        # Cache additive_response computation
        add = ctx.feature("additive_response", perts, params=None)

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            s = 0.0
            for g in targets:
                vals = genes_ann.get(g)
                if vals is not None:
                    v = vals[exon_idx]
                    if v is not None and np.isfinite(v):
                        s += float(v)
            out[i, :, 0] = add[i, :, 0] * s

        out[~np.isfinite(out)] = 0.0
        return out
