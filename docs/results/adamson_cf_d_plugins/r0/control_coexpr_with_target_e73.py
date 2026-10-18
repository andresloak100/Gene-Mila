import numpy as np
from genemila.features.api import Feature, register


@register
class ControlCoexprWithTargetE73(Feature):
    name = "control_coexpr_with_target_e73"
    version = 1
    description = ("Pearson correlation between control expression of gene g and control "
                   "expression of the targeted gene across control cells.")
    rationale = ("Co-expressed genes share regulatory programs, so perturbing the target "
                 "affects correlated genes more.")
    inputs = ["control_cells"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        X = np.asarray(ctx.control_cells, dtype=float)
        if X.ndim != 2 or X.shape[0] < 2:
            return out

        # Center and scale each gene column once (shared across all perturbations).
        Xc = X - X.mean(axis=0, keepdims=True)
        norms = np.sqrt((Xc * Xc).sum(axis=0))
        # Avoid division by zero for constant columns.
        safe_norms = np.where(norms > 0, norms, 1.0)
        Xn = Xc / safe_norms  # unit-norm centered columns

        for i, p in enumerate(perts):
            targets = ctx.target_indices(p)
            if not targets:
                continue
            # Use the first measured target gene as the reference.
            t = targets[0]
            if t < 0 or t >= n_genes:
                continue
            if norms[t] <= 0:
                # Target expression is constant -> no correlation information.
                continue
            # Correlation of every gene with the target column.
            corr = Xn.T @ Xn[:, t]
            corr = np.nan_to_num(corr, nan=0.0, posinf=0.0, neginf=0.0)
            out[i, :, 0] = corr

        return out
