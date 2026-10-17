import numpy as np
from genemila.features.api import Feature, register

@register
class IsTargetTimesTargetLoeufE377(Feature):
    name = "is_target_times_target_loeuf_e377"
    version = 1
    description = "For perturbation p and gene g, if g is a target of p, value is g's LOEUF; otherwise 0."
    rationale = "Loss-of-function intolerance may affect how strongly a gene responds to activation, and this interaction could refine the is_target feature."
    inputs = ["control_cells"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        loeuf = np.zeros(ctx.n_genes, dtype=float)
        have = np.zeros(ctx.n_genes, dtype=bool)

        kd = ctx.knowledge("gene_constraint")
        if kd:
            cols = kd.get("columns", [])
            genes_tbl = kd.get("genes", {})
            if "oe_lof_upper" in cols:
                j = cols.index("oe_lof_upper")
                for g, vals in genes_tbl.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None:
                        continue
                    v = vals[j] if j < len(vals) else None
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        loeuf[gi] = fv
                        have[gi] = True

        for i, p in enumerate(perts):
            idxs = ctx.target_indices(p)
            for gi in idxs:
                if have[gi]:
                    out[i, gi, 0] = loeuf[gi]

        out[~np.isfinite(out)] = 0.0
        return out
