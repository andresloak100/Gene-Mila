import numpy as np
from genemila.features.api import Feature, register

@register
class ControlStdE23(Feature):
    name = "control_std_e23"
    version = 1
    description = "Standard deviation of expression of gene g across control cells."
    rationale = ("Genes with higher expression variability may be more responsive to "
                 "perturbations due to their regulatory plasticity.")
    inputs = ["control_std"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        std = np.asarray(ctx.control_std, dtype=float).ravel()
        if std.shape[0] != ctx.n_genes:
            std = np.resize(std, ctx.n_genes)
        std = np.nan_to_num(std, nan=0.0, posinf=0.0, neginf=0.0)
        out = np.empty((len(perts), ctx.n_genes, 1), dtype=float)
        out[:, :, 0] = std[None, :]
        return out
