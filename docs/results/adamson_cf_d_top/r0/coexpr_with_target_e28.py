import numpy as np
from genemila.features.api import Feature, register


@register
class CoexprWithTargetE28(Feature):
    name = "coexpr_with_target_e28"
    version = 1
    description = ("Pearson correlation across control cells between gene g and the "
                   "perturbation's targeted gene, optionally absolute-valued.")
    rationale = ("Co-expressed genes are often co-regulated; perturbing a regulator "
                 "should affect its co-expressed partners more than unrelated genes.")
    inputs = ["control_cells", "gene_corr"]
    params = {"use_abs": True}
    dim = 1

    def compute(self, ctx, perts, params):
        use_abs = bool(params.get("use_abs", True))
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        corr = ctx.gene_corr
        if corr is None:
            corr = np.corrcoef(ctx.control_cells.T)
        corr = np.asarray(corr, dtype=float)

        # Precompute abs version if needed
        corr_abs = np.abs(corr) if use_abs else corr

        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if not t_idx:
                continue
            # Use the first targeted gene (single-gene targets in this dataset)
            t = int(t_idx[0])
            col = corr_abs[:, t]
            col = np.nan_to_num(col, nan=0.0, posinf=0.0, neginf=0.0)
            out[i, :, 0] = col

        return out
