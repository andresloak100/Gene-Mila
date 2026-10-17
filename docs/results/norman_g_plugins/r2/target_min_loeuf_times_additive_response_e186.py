import numpy as np
from genemila.features.api import Feature, register


@register
class TargetMinLoeufTimesAdditiveResponseE186(Feature):
    name = "target_min_loeuf_times_additive_response_e186"
    version = 1
    description = ("Product of the minimum LOEUF among p's target genes (gnomAD LoF constraint) "
                   "and the additive_response feature.")
    rationale = ("The most LoF-intolerant target may drive stronger downstream effects; "
                 "min LOEUF captures the most constrained target rather than the mean.")
    inputs = ["knowledge", "feature"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1))

        # additive_response baseline
        add = ctx.feature("additive_response", perts)
        add = np.asarray(add, dtype=float)
        if add.ndim == 3:
            add = add[:, :, 0]
        elif add.ndim == 1:
            add = add[:, None]

        # gene_constraint knowledge
        kc = ctx.knowledge("gene_constraint")
        genes_tbl = {}
        cols = []
        if kc is not None:
            genes_tbl = kc.get("genes", {}) or {}
            cols = kc.get("columns", []) or []

        # locate LOEUF column
        loeuf_idx = None
        for j, c in enumerate(cols):
            if "oe_lof_upper" in c.lower() or c.lower() == "loeuf":
                loeuf_idx = j
                break
        if loeuf_idx is None:
            for j, c in enumerate(cols):
                if "loeuf" in c.lower():
                    loeuf_idx = j
                    break

        def gene_loeuf(g):
            if loeuf_idx is None:
                return None
            vals = genes_tbl.get(g)
            if vals is None:
                return None
            try:
                v = vals[loeuf_idx]
            except (IndexError, TypeError):
                return None
            if v is None:
                return None
            try:
                fv = float(v)
            except (TypeError, ValueError):
                return None
            if not np.isfinite(fv):
                return None
            return fv

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p) or []
            vals = [gene_loeuf(g) for g in targets]
            vals = [v for v in vals if v is not None]
            if vals:
                m = float(np.min(vals))
            else:
                m = 0.0
            out[i, :, 0] = m * add[i, :]

        out[~np.isfinite(out)] = 0.0
        return out
