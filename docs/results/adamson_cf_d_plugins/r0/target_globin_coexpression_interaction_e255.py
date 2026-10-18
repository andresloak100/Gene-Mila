import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGlobinCoexpressionInteraction(Feature):
    name = "target_globin_coexpression_interaction_e255"
    version = 1
    description = (
        "For each (p,g), if gene g is a globin gene (HBZ, HBG2, HBA1, HBG1), "
        "the control-cell correlation between the perturbation target gene and g; else 0."
    )
    rationale = (
        "Co-expression in control cells may reflect shared regulatory programs that "
        "are perturbed together; globin genes are expected to be co-regulated with targets."
    )
    inputs = ["gene_corr", "target_indices"]
    params = {}
    dim = 1

    GLOBIN_GENES = ("HBZ", "HBG2", "HBA1", "HBG1")

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1), dtype=float)

        globin_cols = [
            ctx.gene_index[g] for g in self.GLOBIN_GENES if g in ctx.gene_index
        ]
        if not globin_cols:
            return out

        corr = ctx.gene_corr
        globin_cols = np.asarray(globin_cols, dtype=int)

        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if not t_idx:
                continue
            t = int(t_idx[0])
            vals = corr[t, globin_cols]
            vals = np.where(np.isfinite(vals), vals, 0.0)
            out[i, globin_cols, 0] = vals

        return out
