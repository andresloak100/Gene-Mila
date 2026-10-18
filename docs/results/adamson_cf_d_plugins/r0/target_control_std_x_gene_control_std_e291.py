import numpy as np
from genemila.features.api import Feature, register


@register
class TargetControlStdXGeneControlStd(Feature):
    name = "target_control_std_x_gene_control_std_e291"
    version = 1
    description = "Product of control_std of target gene and control_std of gene g."
    rationale = ("Variable genes are more sensitive to perturbations; targeting "
                 "variable genes amplifies effects on other variable genes.")
    inputs = ["control_std", "target_indices"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        gene_std = np.asarray(ctx.control_std, dtype=float)
        gene_std = np.where(np.isfinite(gene_std), gene_std, 0.0)
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if len(t_idx) == 0:
                continue
            t_std = float(np.mean(gene_std[t_idx]))
            out[i, :, 0] = t_std * gene_std
        return out
