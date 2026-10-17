import numpy as np
from genemila.features.api import Feature, register


@register
class TargetCpgTimesControlMean(Feature):
    name = "target_cpg_times_control_mean_e162"
    version = 1
    description = "Product of control_mean of gene g and the mean CpG island promoter score (cpg_oe_promoter) of p's targets."
    rationale = "CpG-rich promoters mark broadly expressed genes; combining target promoter CpG content with baseline expression captures how strongly a perturbation's targets are expressed and thus how much response is possible."
    inputs = ["control_mean", "gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        cpg_col = None
        cpg_values = {}
        if ann is not None:
            cols = ann.get("columns", [])
            if "cpg_oe_promoter" in cols:
                cpg_col = cols.index("cpg_oe_promoter")
            genes_map = ann.get("genes", {}) or {}
            if cpg_col is not None:
                for g, vals in genes_map.items():
                    try:
                        v = vals[cpg_col]
                    except Exception:
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except Exception:
                        continue
                    if np.isfinite(fv):
                        cpg_values[g] = fv

        cm = np.asarray(ctx.control_mean, dtype=float)

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            scores = [cpg_values[g] for g in tg if g in cpg_values]
            if len(scores) > 0:
                mean_cpg = float(np.mean(scores))
            else:
                mean_cpg = 0.0
            out[i, :, 0] = cm * mean_cpg

        out[~np.isfinite(out)] = 0.0
        return out
