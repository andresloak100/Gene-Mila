import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveTimesPromoterCpG(Feature):
    name = "additive_times_promoter_cpg_e420"
    version = 1
    description = "Elementwise product of additive_response and cpg_oe_promoter of gene g."
    rationale = ("CpG islands in promoters are associated with gene regulation; scaling the "
                 "additive response by promoter CpG observed/expected content may capture "
                 "epigenetic modulation of the response.")
    inputs = ["gene_annotation", "additive_response"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        ann = ctx.knowledge("gene_annotation")
        cpg = np.zeros(n, dtype=np.float64)
        if ann is not None:
            genes = ann.get("genes") or {}
            cols = ann.get("columns") or []
            try:
                idx = list(cols).index("cpg_oe_promoter")
            except ValueError:
                idx = None
            if idx is not None:
                for gi, g in enumerate(ctx.genes):
                    vals = genes.get(g)
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
                        cpg[gi] = fv
        cpg = cpg.reshape(1, n, 1)

        add = ctx.feature("additive_response", perts, params=None)
        add = np.asarray(add, dtype=np.float64)
        if add.ndim == 2:
            add = add[:, :, None]
        out = add * cpg
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
