import numpy as np
from genemila.features.api import Feature, register


@register
class TargetPromoterCpgDensityE547(Feature):
    name = "target_promoter_cpg_density_e547"
    version = 1
    description = "Average CpG observed/expected ratio in the promoter of perturbation target gene(s)."
    rationale = (
        "CRISPRa efficacy may depend on chromatin state; CpG-rich promoters are often more "
        "accessible and may respond differently to activation."
    )
    inputs = ["gene_annotation", "target_genes"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        ann = ctx.knowledge("gene_annotation")
        col = None
        if ann is not None:
            cols = ann.get("columns", [])
            if "cpg_oe_promoter" in cols:
                col = cols.index("cpg_oe_promoter")
        genes_ann = ann.get("genes", {}) if ann is not None else {}

        cache = ctx.cache
        if "_cpg_lookup" not in cache:
            lookup = {}
            if col is not None:
                for g, vals in genes_ann.items():
                    try:
                        v = vals[col]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        lookup[g] = fv
            cache["_cpg_lookup"] = lookup
        lookup = cache["_cpg_lookup"]

        # global mean fallback for targets without annotation
        if lookup:
            fallback = float(np.mean(list(lookup.values())))
        else:
            fallback = 0.0

        out = np.zeros((len(perts), ctx.n_genes, 1))
        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            if not tgenes:
                val = fallback
            else:
                vals = [lookup.get(g, fallback) for g in tgenes]
                val = float(np.mean(vals))
            out[i, :, 0] = val
        return out
