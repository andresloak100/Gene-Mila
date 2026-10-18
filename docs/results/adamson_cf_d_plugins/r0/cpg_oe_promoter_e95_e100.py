import numpy as np
from genemila.features.api import Feature, register


@register
class CpgOePromoterE95E100(Feature):
    name = "cpg_oe_promoter_e95_e100"
    version = 1
    description = "Observed/expected CpG ratio in the promoter of gene g from gene_annotation."
    rationale = ("High CpG density in promoters is associated with open chromatin and active "
                 "transcription, making genes more sensitive to perturbation-induced changes.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if not ann:
            return out

        genes_table = ann.get("genes", {}) or {}
        columns = ann.get("columns", []) or []
        try:
            col_idx = columns.index("cpg_oe_promoter")
        except ValueError:
            return out

        # Build per-gene vector aligned to ctx.genes
        vec = np.full(ctx.n_genes, np.nan, dtype=float)
        for g, idx in ctx.gene_index.items():
            vals = genes_table.get(g)
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
                vec[idx] = fv

        # Impute missing with mean of observed (or 0 if none)
        finite_mask = np.isfinite(vec)
        if finite_mask.any():
            fill = float(vec[finite_mask].mean())
        else:
            fill = 0.0
        vec = np.where(finite_mask, vec, fill)

        out[:, :, 0] = vec[None, :]
        return out
