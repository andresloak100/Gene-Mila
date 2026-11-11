import numpy as np
from genemila.features.api import Feature, register


@register
class TargetCoexprAbsE12(Feature):
    name = "target_coexpr_abs_e12"
    version = 1
    description = ("Absolute Pearson correlation between control expression of gene g "
                   "and the perturbation's target gene(s), averaged over targets.")
    rationale = ("Co-expressed genes are co-regulated and thus respond together to "
                 "perturbation of the target.")
    inputs = ["control_cells", "gene_corr"]
    params = {"abs": True}
    dim = 1

    def compute(self, ctx, perts, params, ):
        use_abs = bool(params.get("abs", True))
        n_genes = ctx.n_genes
        corr = np.asarray(ctx.gene_corr, dtype=float)
        # guard against any non-finite values in the cached correlation matrix
        corr = np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)

        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if not t_idx:
                # no measured target -> no co-expression signal
                out[i, :, 0] = 0.0
                continue
            t_idx = np.asarray(t_idx, dtype=int)
            # correlation of every gene with each target: shape (n_targets, n_genes)
            sub = corr[t_idx, :]
            if use_abs:
                sub = np.abs(sub)
            out[i, :, 0] = sub.mean(axis=0)

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
