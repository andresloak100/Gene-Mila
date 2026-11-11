import numpy as np
from genemila.features.api import Feature, register


@register
class MissenseConstraintE47(Feature):
    name = "missense_constraint_e47"
    version = 1
    description = "Standardized missense constraint (oe_mis, oe_mis_upper, mis_z) per gene."
    rationale = ("Genes intolerant to missense variation are more likely to be "
                 "haploinsufficient or essential, so their expression may change more "
                 "upon perturbation.")
    inputs = ["gene_constraint"]
    params = {"columns": ["oe_mis", "oe_mis_upper", "mis_z"]}
    dim = 3

    def compute(self, ctx, perts, params):
        cols = params.get("columns", ["oe_mis", "oe_mis_upper", "mis_z"])
        n_genes = ctx.n_genes
        n_cols = len(cols)

        # Per-gene raw values, NaN where missing.
        raw = np.full((n_genes, n_cols), np.nan, dtype=float)

        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            col_names = kc.get("columns", [])
            col_idx = {}
            for j, c in enumerate(cols):
                if c in col_names:
                    col_idx[j] = col_names.index(c)
            genes_tbl = kc.get("genes", {}) or {}
            for gi, g in enumerate(ctx.genes):
                vals = genes_tbl.get(g)
                if vals is None:
                    continue
                for j, ci in col_idx.items():
                    try:
                        v = vals[ci]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        raw[gi, j] = fv

        # Standardize each column across genes with available values.
        out = np.zeros((n_genes, n_cols), dtype=float)
        for j in range(n_cols):
            col = raw[:, j]
            mask = np.isfinite(col)
            if mask.sum() >= 2:
                mu = col[mask].mean()
                sd = col[mask].std()
                if sd > 0 and np.isfinite(sd):
                    out[mask, j] = (col[mask] - mu) / sd
                else:
                    out[mask, j] = 0.0
            # missing genes stay 0 (neutral, equal to column mean)

        # Broadcast to all perturbations: (n_perts, n_genes, n_cols)
        return np.broadcast_to(out[None, :, :], (len(perts), n_genes, n_cols)).copy()
