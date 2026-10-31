import numpy as np
from genemila.features.api import Feature, register


@register
class AADFraction(Feature):
    name = "aa_d_fraction_e177"
    version = 1
    description = "Fraction of aspartic acid residues in gene g's protein."
    rationale = ("Aspartic acid content may influence protein stability and expression "
                 "response; genes with high aspartic acid fraction may show larger "
                 "expression changes across perturbations.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        n_genes = ctx.n_genes
        out = np.zeros((n_perts, n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if not ann:
            return out

        genes_tbl = ann.get("genes", {})
        columns = ann.get("columns", [])
        try:
            col_idx = columns.index("aa_D")
        except ValueError:
            return out

        # Build gene -> aa_D fraction vector aligned to ctx.genes
        vals = np.full(n_genes, np.nan, dtype=float)
        for gi, g in enumerate(ctx.genes):
            row = genes_tbl.get(g)
            if row is None:
                continue
            try:
                v = row[col_idx]
            except (IndexError, TypeError):
                continue
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv):
                vals[gi] = fv

        # Replace missing with the mean of available values (or 0 if none)
        finite_mask = np.isfinite(vals)
        if finite_mask.any():
            fill = float(vals[finite_mask].mean())
        else:
            fill = 0.0
        vals = np.where(finite_mask, vals, fill)

        out[:, :, 0] = vals[None, :]
        return out
