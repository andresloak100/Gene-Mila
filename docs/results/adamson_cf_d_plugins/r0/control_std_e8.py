import numpy as np
from genemila.features.api import Feature, register

@register
class ControlStdE8(Feature):
    name = "control_std_e8"
    version = 1
    description = "Standard deviation of gene g expression across control cells."
    rationale = ("Genes with higher cell-to-cell variability are more sensitive to "
                 "perturbations or have larger dynamic range, predicting delta magnitude.")
    inputs = ["control_std"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        std = np.asarray(ctx.control_std, dtype=float).ravel()
        if std.shape[0] != ctx.n_genes:
            std = np.zeros(ctx.n_genes, dtype=float)
        std = np.nan_to_num(std, nan=0.0, posinf=0.0, neginf=0.0)
        out = np.empty((len(perts), ctx.n_genes, 1), dtype=float)
        out[:, :, 0] = std[None, :]
        return out
