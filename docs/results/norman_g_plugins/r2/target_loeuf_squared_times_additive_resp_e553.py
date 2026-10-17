import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoeufSquaredTimesAdditiveRespE553(Feature):
    name = "target_loeuf_squared_times_additive_resp_e553"
    version = 1
    description = "Product of additive_response and mean squared LOEUF of p's target genes."
    rationale = ("Squaring LOEUF amplifies differences between tolerant and intolerant targets, "
                 "scaling the additive response by how constrained the targeted genes are.")
    inputs = ["control_cells", "gene_constraint", "train_delta"]
    params = {}
    dim = 1

    def _loeuf_map(self, ctx):
        cache = ctx.cache
        key = "_loeuf_sq_map_e553"
        if key in cache:
            return cache[key]
        loeuf = {}
        kd = ctx.knowledge("gene_constraint")
        if kd is not None:
            genes = kd.get("genes", {}) or {}
            cols = kd.get("columns", []) or []
            if "oe_lof_upper" in cols:
                idx = cols.index("oe_lof_upper")
                for g, vals in genes.items():
                    try:
                        v = vals[idx]
                    except (IndexError, TypeError):
                        v = None
                    if v is not None:
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv):
                            loeuf[g] = fv
        if loeuf:
            med = float(np.median(np.array(list(loeuf.values()), dtype=float)))
        else:
            med = 1.0
        cache[key] = (loeuf, med)
        return cache[key]

    def compute(self, ctx, perts, params):
        loeuf, med = self._loeuf_map(ctx)
        out = np.zeros((len(perts), ctx.n_genes, 1))
        additive = ctx.feature("additive_response", perts)
        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            if tg:
                vals = []
                for g in tg:
                    v = loeuf.get(g, None)
                    if v is None:
                        v = med
                    vals.append(v * v)
                score = float(np.mean(vals))
            else:
                score = med * med
            out[i, :, 0] = score * additive[i, :, 0]
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
