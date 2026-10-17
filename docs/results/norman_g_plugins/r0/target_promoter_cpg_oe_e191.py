import numpy as np
from genemila.features.api import Feature, register


@register
class TargetPromoterCpgOeE191(Feature):
    name = "target_promoter_cpg_oe_e191"
    version = 1
    description = "Average promoter CpG observed/expected ratio (or GC fraction) across the target genes of each perturbation."
    rationale = "CpG-rich promoters are more responsive to CRISPRa, so target promoter CpG content captures target-specific activation potential."
    inputs = ["gene_annotation", "target_genes"]
    params = {"use_gc": False}
    dim = 1

    def compute(self, ctx, perts, params):
        use_gc = bool(params.get("use_gc", False))
        col_name = "gc_promoter" if use_gc else "cpg_oe_promoter"

        ann = ctx.knowledge("gene_annotation")
        values = {}
        col_idx = None
        if ann is not None:
            cols = ann.get("columns", [])
            if col_name in cols:
                col_idx = cols.index(col_name)
            genes_map = ann.get("genes", {}) or {}
            if col_idx is not None:
                for g, vals in genes_map.items():
                    if vals is None:
                        continue
                    try:
                        v = vals[col_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        values[g] = fv

        # Fallback median across all genes in the annotation.
        if len(values) > 0:
            fallback = float(np.median(np.array(list(values.values()), dtype=float)))
        else:
            fallback = 0.0

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            vals = [values[g] for g in targets if g in values]
            if len(vals) > 0:
                out[i, :, 0] = float(np.mean(vals))
            else:
                out[i, :, 0] = fallback
        return out
