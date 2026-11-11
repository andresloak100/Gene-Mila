import numpy as np
from genemila.features.api import Feature, register

@register
class TargetControlStdInteractionE63(Feature):
    name = "target_control_std_interaction_e63"
    version = 1
    description = "Product of is_target and control_std for gene g."
    rationale = ("Target genes with higher baseline variability (control_std) may show "
                 "stronger or more predictable responses to their own perturbation, so an "
                 "interaction between is_target and control_std can capture differential response.")
    inputs = ["control_std"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        std = np.asarray(ctx.control_std, dtype=float).ravel()
        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            tgt = ctx.target_indices(p)
            if tgt:
                idx = np.asarray(tgt, dtype=int)
                vals = std[idx]
                vals = np.where(np.isfinite(vals), vals, 0.0)
                out[i, idx, 0] = vals
        return out
