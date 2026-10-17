import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoeufTimesAdditiveResponse(Feature):
    name = "target_loeuf_times_additive_response_e104"
    version = 1
    description = ("Product of the mean target-gene LOEUF (from gnomAD LoF constraint) "
                   "and the additive_response feature.")
    rationale = ("Essential genes (low LOEUF) may be hubs whose activation yields broader "
                 "downstream effects; scaling the additive baseline by target essentiality "
                 "captures this modulation.")
    inputs = ["knowledge", "feature"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1))

        # additive_response baseline (already leaves p out internally)
        add = ctx.feature("additive_response", perts, None)
        add = np.asarray(add, dtype=float)
        if add.ndim == 3:
            add = add[:, :, 0]
        elif add.ndim == 1:
            add = add[:, None]

        # Load LOEUF per gene from gene_constraint knowledge
        loeuf = self._loeuf_map(ctx)

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            vals = []
            for g in tgenes:
                v = loeuf.get(g)
                if v is not None and np.isfinite(v):
                    vals.append(v)
            if vals:
                mean_loeuf = float(np.mean(vals))
            else:
                mean_loeuf = 1.0
            out[i, :, 0] = add[i] * mean_loeuf

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out

    def _loeuf_map(self, ctx):
        cache = ctx.cache
        key = "_loeuf_map_e104"
        if key in cache:
            return cache[key]
        m = {}
        try:
            kc = ctx.knowledge("gene_constraint")
        except Exception:
            kc = None
        if kc:
            cols = kc.get("columns", [])
            genes = kc.get("genes", {})
            if "oe_lof_upper" in cols:
                idx = cols.index("oe_lof_upper")
                for sym, vals in genes.items():
                    try:
                        v = vals[idx]
                    except Exception:
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except Exception:
                        continue
                    if np.isfinite(fv):
                        m[sym] = fv
        cache[key] = m
        return m
