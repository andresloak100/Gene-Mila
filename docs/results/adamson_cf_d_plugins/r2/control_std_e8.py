import numpy as np
from genemila.features.api import Feature, register

@register
class ControlStdE8(Feature):
    name = "control_std_e8"
    version = 1
    description = "Standard deviation of gene g expression across control cells."
    rationale = ("Genes with higher basal expression variability may be more responsive to "
                 "perturbations due to looser regulation or higher dynamic range.")
    inputs = ["control_cells"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        std = ctx.control_std
        if std is None:
            std = ctx.control_cells.std(axis=0, ddof=1)
        std = np.asarray(std, dtype=float)
        n_genes = ctx.n_genes
        if std.shape[0] != n_genes:
            std = std[:n_genes] if std.shape[0] > n_genes else np.pad(
                std, (0, n_genes - std.shape[0]), mode="edge")
        std = np.where(np.isfinite(std), std, 0.0)
        out = np.empty((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = std[None, :]
        return out
