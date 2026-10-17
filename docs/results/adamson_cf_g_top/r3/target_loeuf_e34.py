import numpy as np
from genemila.features.api import Feature, register

@register
class TargetLoeufE34(Feature):
    name = "target_loeuf_e34"
    version = 1
    description = "LOEUF (oe_lof_upper) of the perturbation's target gene, median-filled."
    rationale = "LoF-intolerant targets (low LOEUF) may drive stronger global responses."
    inputs = ["knowledge", "target_indices"]
    params = {"fill_missing": "median"}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        kc = ctx.knowledge("gene_constraint")
        if kc is None:
            return out
        cols = kc.get("columns", [])
        try:
            idx = cols.index("oe_lof_upper")
        except ValueError:
            return out
        genes = kc.get("genes", {})

        # median fill across all available (finite) LOEUF values
        vals = []
        for g, row in genes.items():
            if row is None or len(row) <= idx:
                continue
            v = row[idx]
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv):
                vals.append(fv)
        fill = float(np.median(vals)) if vals else 0.0

        # cache per-target LOEUF lookups
        cache = ctx.cache.setdefault("target_loeuf_e34", {})
        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            val = None
            for tg in tgenes:
                if tg in cache:
                    v = cache[tg]
                else:
                    row = genes.get(tg)
                    v = None
                    if row is not None and len(row) > idx and row[idx] is not None:
                        try:
                            fv = float(row[idx])
                            if np.isfinite(fv):
                                v = fv
                        except (TypeError, ValueError):
                            v = None
                    cache[tg] = v
                if v is not None:
                    val = v
                    break
            if val is None:
                val = fill
            out[i, :, 0] = val
        return out
