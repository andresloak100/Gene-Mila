import numpy as np
from genemila.features.api import Feature, register


@register
class GeneCorrTargetE24(Feature):
    name = "gene_corr_target_e24"
    version = 1
    description = "Correlation between each gene and the perturbation target gene across control cells."
    rationale = "Co-expressed genes may share regulatory programs, so perturbing one may affect the other."
    inputs = ["gene_corr", "control_cells"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))
        corr = ctx.gene_corr
        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if not t_idx:
                continue
            t = t_idx[0]
            out[i, :, 0] = corr[:, t]
        return out
