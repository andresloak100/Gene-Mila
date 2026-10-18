import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGeneControlCorrE261(Feature):
    name = "target_gene_control_corr_e261"
    version = 1
    description = "Absolute control-cell correlation between perturbation target gene and gene g."
    rationale = ("Genes co-expressed across control cells are likely co-regulated, so perturbing "
                 "one may affect the other; the target's correlation with g captures this link.")
    inputs = ["gene_corr", "control_cells"]
    params = {"abs": True}
    dim = 1

    def compute(self, ctx, perts, params):
        use_abs = bool(params.get("abs", True))
        corr = ctx.gene_corr
        if corr is None:
            corr = np.zeros((ctx.n_genes, ctx.n_genes), dtype=float)
        corr = np.asarray(corr, dtype=float)
        if use_abs:
            corr = np.abs(corr)

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if not t_idx:
                continue
            valid = [t for t in t_idx if 0 <= t < ctx.n_genes]
            if not valid:
                continue
            # mean over target columns -> (n_genes,)
            row = corr[valid, :].mean(axis=0)
            out[i, :, 0] = row
            # ensure target genes themselves are 1 (self-correlation)
            for t in valid:
                out[i, t, 0] = 1.0
        return out
