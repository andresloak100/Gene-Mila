import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoeufMeanE85(Feature):
    name = "target_loeuf_mean_e85"
    version = 1
    description = "Average LOEUF (oe_lof_upper) across the perturbation's target genes."
    rationale = ("LoF-intolerant genes (low LOEUF) are under strong constraint and may have "
                 "more extensive downstream regulatory networks, amplifying the CRISPRa response. "
                 "Averaging over both targets of a pair gives an order-invariant summary.")
    inputs = ["knowledge", "target_genes"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        kc = ctx.cache.get("_loeuf_e85_map")
        if kc is None:
            kc = {}
            data = ctx.knowledge("gene_constraint")
            if data:
                cols = data.get("columns", [])
                genes = data.get("genes", {}) or {}
                try:
                    ci = cols.index("oe_lof_upper")
                except ValueError:
                    ci = None
                if ci is not None:
                    for g, vals in genes.items():
                        if vals is None:
                            continue
                        try:
                            v = vals[ci]
                        except (IndexError, TypeError):
                            continue
                        if v is None:
                            continue
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv):
                            kc[g] = fv
            ctx.cache["_loeuf_e85_map"] = kc

        for i, p in enumerate(perts):
            vals = []
            for g in ctx.target_genes(p):
                v = kc.get(g)
                if v is not None:
                    vals.append(v)
            if vals:
                out[i, :, 0] = float(np.mean(vals))
            else:
                out[i, :, 0] = np.nan

        out[~np.isfinite(out)] = 0.0
        return out
