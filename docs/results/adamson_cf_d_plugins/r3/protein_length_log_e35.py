import numpy as np
from genemila.features.api import Feature, register


@register
class ProteinLengthLogE35(Feature):
    name = "protein_length_log_e35"
    version = 1
    description = "Log10 of protein_length (from protein_annotation) plus 1, per gene."
    rationale = (
        "Longer proteins require longer transcripts, which are more costly to produce "
        "and less efficiently maintained under perturbation, so genes encoding longer "
        "proteins may show smaller expression changes."
    )
    inputs = ["protein_annotation.protein_length"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        n_genes = ctx.n_genes
        out = np.zeros((n_perts, n_genes, 1), dtype=float)

        ann = ctx.knowledge("protein_annotation")
        if ann is None:
            return out

        genes_map = ann.get("genes", {})
        columns = ann.get("columns", [])

        try:
            col_idx = columns.index("protein_length")
        except ValueError:
            return out

        vals = np.zeros(n_genes, dtype=float)
        for j, g in enumerate(ctx.genes):
            row = genes_map.get(g)
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
            if not np.isfinite(fv):
                continue
            vals[j] = np.log10(fv + 1.0)

        out[:, :, 0] = vals[None, :]
        return out
