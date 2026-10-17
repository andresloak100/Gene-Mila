import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoeufE544(Feature):
    name = "target_loeuf_e544"
    version = 1
    description = "Average LOEUF (oe_lof_upper) of the perturbation's target gene(s); median-imputed when missing."
    rationale = "LoF-intolerant (low LOEUF) genes are dosage-sensitive; activating them may yield stronger or more specific downstream responses."
    inputs = ["knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.full((len(perts), ctx.n_genes, 1), np.nan, dtype=float)

        kc = ctx.knowledge("gene_constraint")
        loeuf = {}
        if kc is not None:
            genes = kc.get("genes", {}) or {}
            cols = kc.get("columns", []) or []
            try:
                idx = cols.index("oe_lof_upper")
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
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        loeuf[g] = fv

        if loeuf:
            median = float(np.median(np.array(list(loeuf.values()), dtype=float)))
        else:
            median = 0.0

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            if not tgenes:
                val = median
            else:
                vals = [loeuf.get(g, median) for g in tgenes]
                val = float(np.mean(vals))
            out[i, :, 0] = val

        out = np.nan_to_num(out, nan=median, posinf=median, neginf=median)
        return out
