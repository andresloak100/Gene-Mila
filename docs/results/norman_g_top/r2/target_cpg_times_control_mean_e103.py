import numpy as np
from genemila.features.api import Feature, register


@register
class TargetCpgTimesControlMean(Feature):
    name = "target_cpg_times_control_mean_e103"
    version = 1
    description = "Product of the perturbation targets' mean promoter CpG o/e ratio and gene g's control mean expression."
    rationale = "CRISPRa efficacy may depend on target promoter CpG density and interact with basal expression of downstream genes."
    inputs = ["control_mean", "target_genes"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        cpg = {}
        if ann is not None:
            genes = ann.get("genes", {})
            cols = ann.get("columns", [])
            try:
                idx = cols.index("cpg_oe_promoter")
            except ValueError:
                idx = None
            if idx is not None:
                for g, vals in genes.items():
                    if vals is None:
                        continue
                    try:
                        v = vals[idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        v = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(v):
                        cpg[g] = v

        cm = np.asarray(ctx.control_mean, dtype=float)
        cm = np.where(np.isfinite(cm), cm, 0.0)

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            vals = [cpg[g] for g in tgenes if g in cpg]
            if vals:
                cpg_val = float(np.mean(vals))
            else:
                cpg_val = 0.0
            out[i, :, 0] = cpg_val * cm
        return out
