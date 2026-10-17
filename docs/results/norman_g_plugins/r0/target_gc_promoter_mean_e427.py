import numpy as np
from genemila.features.api import Feature, register

@register
class TargetGCPromoterMean(Feature):
    name = "target_gc_promoter_mean_e427"
    version = 1
    description = "Mean gc_promoter of the target genes of each perturbation."
    rationale = ("GC-rich promoters may be more accessible or responsive to CRISPRa, "
                 "modulating activation strength and downstream responses.")
    inputs = ["knowledge:gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        ann = ctx.knowledge("gene_annotation")
        out = np.zeros((len(perts), ctx.n_genes, 1))

        gc_vals = {}
        if ann is not None:
            genes_tbl = ann.get("genes", {})
            columns = ann.get("columns", [])
            try:
                gc_idx = columns.index("gc_promoter")
            except ValueError:
                gc_idx = None
            if gc_idx is not None:
                for sym, vals in genes_tbl.items():
                    try:
                        v = vals[gc_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        gc_vals[sym] = fv

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            vals = [gc_vals[g] for g in tgenes if g in gc_vals]
            if vals:
                out[i, :, 0] = float(np.mean(vals))
            else:
                out[i, :, 0] = 0.0
        return out
