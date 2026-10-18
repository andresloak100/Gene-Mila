import numpy as np
from genemila.features.api import Feature, register


@register
class ControlStdE11(Feature):
    name = "control_std_e11"
    version = 1
    description = "Standard deviation of gene expression across control cells."
    rationale = (
        "High expression variability across control cells indicates less tight "
        "regulation, allowing larger responses to perturbation."
    )
    inputs = ["control_cells", "control_std"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        std = np.asarray(ctx.control_std, dtype=float).ravel()
        if std.shape[0] != n or not np.all(np.isfinite(std)):
            cc = np.asarray(ctx.control_cells, dtype=float)
            std = np.nanstd(cc, axis=0) if cc.shape[0] > 0 else np.zeros(n)
        std = np.where(np.isfinite(std), std, 0.0)
        out = np.empty((len(perts), n, 1), dtype=float)
        out[:, :, 0] = std[None, :]
        return out
