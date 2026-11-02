import numpy as np
from genemila.features.api import Feature, register


@register
class ControlStdE21(Feature):
    name = "control_std_e21"
    version = 1
    description = "Standard deviation of expression of gene g across control cells."
    rationale = ("Genes with high expression variability in control cells may have larger "
                 "perturbation responses or be less predictable.")
    inputs = ["control_cells"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        std = np.asarray(ctx.control_std, dtype=float).ravel()
        std = np.where(np.isfinite(std), std, 0.0)
        out = np.broadcast_to(std[None, :, None], (len(perts), ctx.n_genes, 1)).copy()
        return out
