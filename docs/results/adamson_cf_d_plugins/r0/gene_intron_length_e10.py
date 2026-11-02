import numpy as np
from genemila.features.api import Feature, register


@register
class GeneIntronLengthE10(Feature):
    name = "gene_intron_length_e10"
    version = 1
    description = "Intron length in kb for gene g from gene_annotation."
    rationale = ("Longer introns correlate with lower expression or different regulatory "
                 "complexity, affecting response to perturbations.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is None:
            return out

        columns = ann.get("columns", [])
        genes_tbl = ann.get("genes", {})
        try:
            col_idx = columns.index("intron_length_kb")
        except ValueError:
            return out

        # Build per-gene vector aligned to ctx.genes
        vec = np.full(ctx.n_genes, np.nan, dtype=float)
        for g, col in ctx.gene_index.items():
            vals = genes_tbl.get(g)
            if vals is None:
                continue
            try:
                v = vals[col_idx]
            except (IndexError, TypeError):
                continue
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv):
                vec[col] = fv

        # Impute missing with mean of available values, else 0
        finite_mask = np.isfinite(vec)
        if finite_mask.any():
            fill = float(vec[finite_mask].mean())
        else:
            fill = 0.0
        vec[~finite_mask] = fill

        out[:, :, 0] = vec[None, :]
        return out
