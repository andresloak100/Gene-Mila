import numpy as np
from genemila.features.api import Feature, register


@register
class AAGlycineFraction(Feature):
    name = "aa_g_fraction_e178"
    version = 1
    description = "Fraction of glycine residues in gene g's protein (gene_annotation aa_G column)."
    rationale = (
        "Glycine-rich proteins are often structural and less regulated, so their "
        "expression may change less upon perturbation; aa_G captures this per gene."
    )
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        ann = ctx.knowledge("gene_annotation")
        col_vals = np.full(n_genes, np.nan, dtype=float)

        if ann is not None:
            genes_tab = ann.get("genes", {}) if isinstance(ann, dict) else {}
            columns = ann.get("columns", []) if isinstance(ann, dict) else []
            idx = None
            for j, c in enumerate(columns):
                if c == "aa_G":
                    idx = j
                    break
            if idx is not None:
                for g, gi in ctx.gene_index.items():
                    vals = genes_tab.get(g)
                    if vals is None:
                        continue
                    try:
                        v = vals[idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        col_vals[gi] = fv

        # Fallback: use mean of observed values for missing entries
        finite_mask = np.isfinite(col_vals)
        if finite_mask.any():
            fill = float(col_vals[finite_mask].mean())
        else:
            fill = 0.0
        col_vals = np.where(finite_mask, col_vals, fill)

        out[:, :, 0] = col_vals[None, :]
        return out
