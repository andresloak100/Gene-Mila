import numpy as np
from genemila.features.api import Feature, register


@register
class TargetCpGOePromoterE352(Feature):
    name = "target_cpg_oe_promoter_e352"
    version = 1
    description = "CpG observed/expected ratio of the perturbation target's promoter."
    rationale = ("Genes with strong CpG islands in their promoters are under tighter "
                 "epigenetic control and may respond more strongly to perturbation.")
    inputs = ["knowledge:gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        col = None
        genes_map = None
        if ann is not None:
            genes_map = ann.get("genes", {}) if isinstance(ann, dict) else None
            columns = ann.get("columns", []) if isinstance(ann, dict) else []
            if "cpg_oe_promoter" in columns:
                col = columns.index("cpg_oe_promoter")

        # Build target -> value mapping, collect values for median fallback.
        target_vals = {}
        all_vals = []
        if genes_map is not None and col is not None:
            for p in perts:
                tgenes = ctx.target_genes(p)
                if not tgenes:
                    continue
                t = tgenes[0]
                if t in target_vals:
                    continue
                entry = genes_map.get(t)
                val = None
                if entry is not None and col < len(entry):
                    v = entry[col]
                    if v is not None:
                        try:
                            fv = float(v)
                            if np.isfinite(fv):
                                val = fv
                        except (TypeError, ValueError):
                            val = None
                target_vals[t] = val
                if val is not None:
                    all_vals.append(val)

        if all_vals:
            median = float(np.median(np.array(all_vals, dtype=float)))
        else:
            median = 0.0

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            val = median
            if tgenes:
                v = target_vals.get(tgenes[0])
                if v is not None:
                    val = v
            out[i, :, 0] = val

        return out
