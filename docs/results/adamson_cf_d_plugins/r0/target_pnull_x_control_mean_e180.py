import numpy as np
from genemila.features.api import Feature, register


@register
class TargetPnullXControlMean(Feature):
    name = "target_pnull_x_control_mean_e180"
    version = 1
    description = "Product of target gene's pNull and gene g's control_mean."
    rationale = ("Targets under less constraint (higher pNull) may perturb highly expressed "
                 "genes more strongly, reflecting buffering capacity.")
    inputs = ["control_mean", "gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        cm = np.asarray(ctx.control_mean, dtype=float)
        cm = np.where(np.isfinite(cm), cm, 0.0)

        kc = ctx.knowledge("gene_constraint")
        pnull_map = {}
        if kc is not None:
            cols = kc.get("columns", [])
            genes = kc.get("genes", {})
            if "pNull" in cols:
                j = cols.index("pNull")
                for g, vals in genes.items():
                    if vals is None:
                        continue
                    try:
                        v = vals[j]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        pnull_map[g] = fv

        for i, p in enumerate(perts):
            pnull = 0.0
            for tg in ctx.target_genes(p):
                if tg in pnull_map:
                    pnull = pnull_map[tg]
                    break
            out[i, :, 0] = pnull * cm
        return out
