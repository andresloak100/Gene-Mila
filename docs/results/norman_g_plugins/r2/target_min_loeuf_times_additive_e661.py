import numpy as np
from genemila.features.api import Feature, register


@register
class TargetMinLoeufTimesAdditiveE661(Feature):
    name = "target_min_loeuf_times_additive_e661"
    version = 1
    description = ("Product of additive_response and the minimum LOEUF score among "
                   "p's target genes (lower LOEUF = more essential).")
    rationale = ("If one target is highly essential (low LOEUF), its activation may "
                 "dominate the response, so the most essential target can act as a "
                 "bottleneck that scales the additive baseline.")
    inputs = ["knowledge", "feature"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        # additive_response feature (n_perts, n_genes, 1)
        add = ctx.feature("additive_response", perts)
        add = np.asarray(add, dtype=float)
        if add.ndim == 2:
            add = add[:, :, None]

        # load LOEUF column from gnomAD constraint knowledge
        loeuf_map = {}
        cache = ctx.cache
        key = "_loeuf_map_e661"
        if key in cache:
            loeuf_map = cache[key]
        else:
            kn = ctx.knowledge("gene_constraint")
            if kn is not None:
                cols = kn.get("columns", [])
                genes_tbl = kn.get("genes", {})
                if "oe_lof_upper" in cols:
                    idx = cols.index("oe_lof_upper")
                    for g, vals in genes_tbl.items():
                        if vals is None:
                            continue
                        try:
                            v = vals[idx]
                        except (IndexError, TypeError):
                            continue
                        if v is None:
                            continue
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv):
                            loeuf_map[g] = fv
            cache[key] = loeuf_map

        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            vals = [loeuf_map[g] for g in tg if g in loeuf_map]
            if vals:
                scale = float(np.min(vals))
            else:
                scale = 1.0
            out[i, :, 0] = add[i, :, 0] * scale

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
