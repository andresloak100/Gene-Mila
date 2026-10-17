import numpy as np
from genemila.features.api import Feature, register

@register
class TargetPromoterCpGDensity(Feature):
    name = "target_promoter_cpg_density_e167"
    version = 1
    description = "CpG observed/expected ratio of the perturbation target's promoter, median-filled."
    rationale = "Targets with high promoter CpG density may be more methylation-regulated and show stronger perturbation effects."
    inputs = ["gene_annotation", "target_indices"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        ann = ctx.knowledge("gene_annotation")
        col = None
        vals = {}
        if ann is not None:
            cols = ann.get("columns", [])
            try:
                col = cols.index("cpg_oe_promoter")
            except ValueError:
                col = None
            genes = ann.get("genes", {})
            if col is not None:
                for g, row in genes.items():
                    if row is not None and len(row) > col and row[col] is not None:
                        try:
                            v = float(row[col])
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(v):
                            vals[g] = v

        if vals:
            fill = float(np.median(list(vals.values())))
        else:
            fill = 0.0

        out = np.full((len(perts), ctx.n_genes, 1), fill, dtype=float)
        for i, p in enumerate(perts):
            for tg in ctx.target_genes(p):
                if tg in vals:
                    out[i, :, 0] = vals[tg]
                    break
        return out
