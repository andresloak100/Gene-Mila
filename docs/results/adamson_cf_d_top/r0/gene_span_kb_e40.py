import numpy as np
from genemila.features.api import Feature, register


@register
class GeneSpanKbE40(Feature):
    name = "gene_span_kb_e40"
    version = 1
    description = "Gene span in kb for gene g from gene_annotation."
    rationale = (
        "Longer genes may have more regulatory complexity or slower transcriptional "
        "response, attenuating expression changes; residual analysis shows negative "
        "correlation of response with gene_span_kb."
    )
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        out = np.zeros((n_perts, ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is None:
            return out

        columns = ann.get("columns", [])
        try:
            col_idx = columns.index("gene_span_kb")
        except ValueError:
            return out

        genes_tbl = ann.get("genes", {}) or {}

        # Map each ctx gene to its gene_span_kb value (NaN if missing).
        span = np.full(ctx.n_genes, np.nan, dtype=float)
        for gi, g in enumerate(ctx.genes):
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
                span[gi] = fv

        # Fill missing values with the mean of observed values (finite only).
        finite_mask = np.isfinite(span)
        if finite_mask.any():
            fill = float(span[finite_mask].mean())
        else:
            fill = 0.0
        span = np.where(finite_mask, span, fill)

        # Same value for every perturbation row.
        out[:, :, 0] = span[None, :]
        return out
