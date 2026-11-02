import numpy as np
from genemila.features.api import Feature, register


@register
class NExonsDirectE117(Feature):
    name = "n_exons_direct_e117"
    version = 1
    description = "Numeric feature: n_exons value from gene_annotation for gene g."
    rationale = (
        "Genes with more exons may have more complex regulation and larger dynamic "
        "range, potentially leading to larger transcriptional responses upon perturbation."
    )
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is None:
            return out

        genes_tbl = ann.get("genes", {})
        columns = ann.get("columns", [])
        try:
            col_idx = columns.index("n_exons")
        except ValueError:
            return out

        # Build per-gene n_exons vector aligned to ctx.genes
        values = np.full(ctx.n_genes, np.nan, dtype=float)
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
                values[gi] = fv

        # Fill missing with column mean (finite) or 0
        finite_mask = np.isfinite(values)
        if finite_mask.any():
            fill = float(values[finite_mask].mean())
        else:
            fill = 0.0
        values = np.where(finite_mask, values, fill)

        out[:, :, 0] = values[None, :]
        return out
