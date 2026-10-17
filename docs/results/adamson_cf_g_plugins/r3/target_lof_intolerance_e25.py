import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLofIntoleranceE25(Feature):
    name = "target_lof_intolerance_e25"
    version = 1
    description = "LOEUF (oe_lof_upper) of the perturbation's target gene; default when missing."
    rationale = ("LoF-intolerant (low LOEUF / essential) targets may cause larger global "
                 "expression changes upon knockdown.")
    inputs = ["knowledge:gene_constraint"]
    params = {"default_value": 1.0}
    dim = 1

    def compute(self, ctx, perts, params):
        default_value = float(params.get("default_value", 1.0))
        out = np.full((len(perts), ctx.n_genes, 1), default_value, dtype=float)

        kc = ctx.knowledge("gene_constraint")
        if kc is None:
            return out

        genes = kc.get("genes", {}) or {}
        columns = list(kc.get("columns", []) or [])
        try:
            loeuf_idx = columns.index("oe_lof_upper")
        except ValueError:
            loeuf_idx = None
        try:
            pli_idx = columns.index("pLI")
        except ValueError:
            pli_idx = None

        def lookup(symbol):
            vals = genes.get(symbol)
            if vals is None:
                return default_value
            if loeuf_idx is not None and loeuf_idx < len(vals):
                v = vals[loeuf_idx]
                if v is not None:
                    try:
                        fv = float(v)
                        if np.isfinite(fv):
                            return fv
                    except (TypeError, ValueError):
                        pass
            if pli_idx is not None and pli_idx < len(vals):
                v = vals[pli_idx]
                if v is not None:
                    try:
                        fv = float(v)
                        if np.isfinite(fv):
                            # inverse pLI: high pLI -> low value (intolerant)
                            return 1.0 - fv
                    except (TypeError, ValueError):
                        pass
            return default_value

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            if not tg:
                continue
            score = lookup(tg[0])
            if not np.isfinite(score):
                score = default_value
            out[i, :, 0] = score

        return out
