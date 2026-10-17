import numpy as np
from genemila.features.api import Feature, register


@register
class TargetPromoterCpgStrengthXMeanRespE163(Feature):
    name = "target_promoter_cpg_strength_x_mean_resp_e163"
    version = 1
    description = "Product of target gene promoter CpG strength and mean_response for gene g."
    rationale = ("Genes with high average response may be more sensitive to perturbations of "
                 "genes with strong CpG promoters; the interaction captures context-dependent "
                 "amplification of the generic response program.")
    inputs = ["control_cells", "train_delta", "knowledge"]
    params = {}
    dim = 1

    def _promoter_cpg(self, ctx):
        cache = ctx.cache
        key = "e163_promoter_cpg"
        if key in cache:
            return cache[key]
        arr = np.zeros(ctx.n_genes, dtype=float)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            cols = ann.get("columns", [])
            genes = ann.get("genes", {})
            if "cpg_oe_promoter" in cols:
                j = cols.index("cpg_oe_promoter")
                for g, vals in genes.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None or vals is None:
                        continue
                    v = vals[j] if j < len(vals) else None
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        arr[gi] = fv
        cache[key] = arr
        return arr

    def compute(self, ctx, perts, params):
        n = len(perts)
        promoter_cpg = self._promoter_cpg(ctx)
        out = np.zeros((n, ctx.n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            mean_resp = d.mean(axis=0)
            t_idx = ctx.target_indices(p)
            if t_idx:
                strength = float(np.mean(promoter_cpg[t_idx]))
            else:
                strength = 0.0
            if not np.isfinite(strength):
                strength = 0.0
            out[i, :, 0] = strength * mean_resp

        out[~np.isfinite(out)] = 0.0
        return out
