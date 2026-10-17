import numpy as np
from genemila.features.api import Feature, register


@register
class TargetPromoterCpGContentE180(Feature):
    name = "target_promoter_cpg_content_e180"
    version = 1
    description = "Average promoter CpG content (gc_promoter or cpg_oe_promoter) of p's target genes."
    rationale = "CRISPRa efficiency may depend on promoter CpG density/methylation; averaging over targets captures this."
    inputs = ["gene_annotation", "target_genes"]
    params = {"promoter_metric": "gc_promoter"}
    dim = 1

    def compute(self, ctx, perts, params):
        metric = params.get("promoter_metric", "gc_promoter")
        if metric not in ("gc_promoter", "cpg_oe_promoter"):
            metric = "gc_promoter"

        ann = ctx.knowledge("gene_annotation")
        gene_vals = {}
        if ann is not None:
            cols = ann.get("columns", [])
            genes = ann.get("genes", {})
            if metric in cols:
                mi = cols.index(metric)
                for g, vals in genes.items():
                    if vals is None:
                        continue
                    try:
                        v = vals[mi]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        gene_vals[g] = fv

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue
            vals = [gene_vals[t] for t in targets if t in gene_vals]
            if not vals:
                continue
            out[i, :, 0] = float(np.mean(vals))
        return out
