import numpy as np
from genemila.features.api import Feature, register


@register
class GeneConstraintRandomProjectionE74(Feature):
    name = "gene_constraint_random_projection_e74"
    version = 1
    description = ("Random Gaussian projection of standardized gene_constraint columns "
                   "(oe_lof_lower, pNull, pRec, syn_z, lof_z, obs_lof, exp_lof, "
                   "oe_lof_upper_bin) into a low-dimensional space.")
    rationale = ("Constraint metrics may jointly encode gene essentiality and dosage "
                 "sensitivity; a random projection captures joint nonlinear structure "
                 "that single columns miss.")
    inputs = ["gene_constraint"]
    params = {"n_components": 10, "seed": 74}
    dim = 10

    def compute(self, ctx, perts, params):
        n_components = int(params.get("n_components", 10))
        seed = int(params.get("seed", 74))

        kc = ctx.knowledge("gene_constraint")
        n_genes = ctx.n_genes
        n_comp = n_components

        # Build gene x column matrix of constraint values (NaN where missing).
        cols_wanted = ["oe_lof_lower", "pNull", "pRec", "syn_z", "lof_z",
                       "obs_lof", "exp_lof", "oe_lof_upper_bin"]
        if kc is None:
            mat = np.zeros((n_genes, len(cols_wanted)), dtype=float)
        else:
            columns = list(kc.get("columns", []))
            col_idx = {c: i for i, c in enumerate(columns)}
            genes_tbl = kc.get("genes", {}) or {}
            mat = np.full((n_genes, len(cols_wanted)), np.nan, dtype=float)
            for gi, g in enumerate(ctx.genes):
                vals = genes_tbl.get(g)
                if vals is None:
                    continue
                for j, c in enumerate(cols_wanted):
                    if c in col_idx and col_idx[c] < len(vals):
                        v = vals[col_idx[c]]
                        if v is not None:
                            try:
                                fv = float(v)
                            except (TypeError, ValueError):
                                continue
                            if np.isfinite(fv):
                                mat[gi, j] = fv

        # Standardize each column across genes (ignoring NaNs), impute NaN -> 0.
        n_cols = mat.shape[1]
        Z = np.zeros((n_genes, n_cols), dtype=float)
        for j in range(n_cols):
            col = mat[:, j]
            mask = np.isfinite(col)
            if mask.sum() >= 2:
                mu = col[mask].mean()
                sd = col[mask].std()
                if sd > 1e-12:
                    Z[mask, j] = (col[mask] - mu) / sd
                # else leave zeros
            # else leave zeros

        # Gaussian random projection matrix (n_cols x n_comp), fixed seed.
        rng = np.random.RandomState(seed)
        R = rng.randn(n_cols, n_comp) / np.sqrt(max(n_cols, 1))

        proj = Z @ R  # (n_genes, n_comp)

        # Same projection for every perturbation row (gene-level feature).
        out = np.empty((len(perts), n_genes, n_comp), dtype=float)
        for i in range(len(perts)):
            out[i] = proj

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
