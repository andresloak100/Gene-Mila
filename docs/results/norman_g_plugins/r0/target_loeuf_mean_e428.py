import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoeufMeanE428(Feature):
    name = "target_loeuf_mean_e428"
    version = 1
    description = "Mean LOEUF (oe_lof_upper) of the perturbation's target genes."
    rationale = ("Perturbing LoF-intolerant (low LOEUF) genes may produce larger "
                 "expression changes; this encodes target essentiality per perturbation.")
    inputs = ["knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        # Load constraint table once and cache the per-gene LOEUF lookup.
        cache = ctx.cache
        if "_loeuf_map_e428" not in cache:
            loeuf_map = {}
            kc = ctx.knowledge("gene_constraint")
            if kc is not None:
                cols = kc.get("columns", [])
                try:
                    loeuf_idx = cols.index("oe_lof_upper")
                except ValueError:
                    loeuf_idx = None
                genes = kc.get("genes", {})
                if loeuf_idx is not None:
                    for sym, vals in genes.items():
                        if vals is None:
                            continue
                        try:
                            v = vals[loeuf_idx]
                        except (IndexError, TypeError):
                            continue
                        if v is None:
                            continue
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv):
                            loeuf_map[sym] = fv
            cache["_loeuf_map_e428"] = loeuf_map
        loeuf_map = cache["_loeuf_map_e428"]

        # Global fallback: mean LOEUF over genes with a value.
        if loeuf_map:
            fallback = float(np.mean(list(loeuf_map.values())))
        else:
            fallback = 1.0

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            vals = [loeuf_map[g] for g in targets if g in loeuf_map]
            if vals:
                val = float(np.mean(vals))
            else:
                val = fallback
            out[i, :, 0] = val

        return out
