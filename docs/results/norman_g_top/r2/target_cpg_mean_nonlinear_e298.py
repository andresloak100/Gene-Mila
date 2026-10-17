import numpy as np
from genemila.features.api import Feature, register

@register
class TargetCpgMeanNonlinearE298(Feature):
    name = "target_cpg_mean_nonlinear_e298"
    version = 1
    description = "Square of the mean cpg_oe_promoter of the perturbation's target genes."
    rationale = ("CRISPRa efficiency depends on promoter context; squaring the mean CpG "
                 "promoter score captures nonlinear saturation of activation at accessible loci.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))
        ann = ctx.knowledge("gene_annotation")
        if ann is None:
            return out
        genes = ann.get("genes", {})
        cols = ann.get("columns", [])
        try:
            ci = cols.index("cpg_oe_promoter")
        except ValueError:
            return out

        # Precompute per-gene cpg score (NaN -> ignored)
        score = np.full(ctx.n_genes, np.nan)
        for g, gi in ctx.gene_index.items():
            vals = genes.get(g)
            if vals is None:
                continue
            v = vals[ci]
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv):
                score[gi] = fv

        for i, p in enumerate(perts):
            idx = ctx.target_indices(p)
            if not idx:
                continue
            vals = score[idx]
            vals = vals[np.isfinite(vals)]
            if vals.size == 0:
                continue
            m = vals.mean()
            out[i, :, 0] = m * m
        return out
