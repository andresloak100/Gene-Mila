import numpy as np
from genemila.features.api import Feature, register


@register
class TargetPromoterCpGIsland(Feature):
    name = "target_promoter_cpg_island_e534"
    version = 2
    description = "Mean CpG observed/expected ratio at the promoters of the perturbation's target genes (0 if unknown)."
    rationale = "CpG island promoters are active; CRISPRa may be more effective at such loci, yielding stronger effects. Using a continuous CpG o/e value preserves variation across perturbations."
    inputs = ["knowledge:gene_annotation"]
    params = {"default": 0.0}
    dim = 1

    def compute(self, ctx, perts, params):
        default = float(params.get("default", 0.0))
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        cpg_map = {}
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            columns = ann.get("columns", [])
            genes = ann.get("genes", {})
            if "cpg_oe_promoter" in columns:
                idx = columns.index("cpg_oe_promoter")
                for sym, vals in genes.items():
                    try:
                        v = vals[idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        cpg_map[sym] = float(v)
                    except (TypeError, ValueError):
                        continue

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            vals = []
            for t in targets:
                v = cpg_map.get(t)
                if v is not None:
                    vals.append(v)
            if vals:
                score = float(np.mean(vals))
            else:
                score = default
            out[i, :, 0] = score

        return out
