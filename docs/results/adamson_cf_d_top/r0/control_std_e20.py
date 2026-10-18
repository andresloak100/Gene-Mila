import numpy as np
from genemila.features.api import Feature, register

@register
class ControlStdE20(Feature):
    name = "control_std_e20"
    version = 1
    description = "Standard deviation of control expression for gene g across control cells."
    rationale = ("Genes with higher basal expression variability are less tightly buffered "
                 "and thus show larger responses to perturbations.")
    inputs = ["control_std"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        std = np.asarray(ctx.control_std, dtype=float).ravel()
        if std.shape[0] != ctx.n_genes:
            std = np.nan_to_num(std, nan=0.0, posinf=0.0, neginf=0.0)
            if std.shape[0] < ctx.n_genes:
                std = np.concatenate([std, np.zeros(ctx.n_genes - std.shape[0])])
            else:
                std = std[:ctx.n_genes]
        std = np.nan_to_num(std, nan=0.0, posinf=0.0, neginf=0.0)
        out = np.empty((len(perts), ctx.n_genes, 1), dtype=float)
        out[:, :, 0] = std[None, :]
        return out
