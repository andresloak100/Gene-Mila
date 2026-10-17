import numpy as np
from genemila.features.api import Feature, register

@register
class AdditiveResponseXGeneSpanE128(Feature):
    name = "additive_response_x_gene_span_e128"
    version = 1
    description = "Product of additive_response and gene_span_kb of gene g."
    rationale = "Chromatin context and transcript complexity affect CRISPRa efficiency and downstream expression changes."
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        n_perts = len(perts)

        # additive_response feature: shape (n_perts, n_genes, 1)
        add = ctx.feature("additive_response", perts)
        if add.ndim == 3:
            add = add[:, :, 0]
        elif add.ndim == 1:
            add = add[:, None]

        # gene_span_kb per gene from gene_annotation
        span = np.full(n_genes, np.nan, dtype=np.float64)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes_ann = ann.get("genes", {})
            columns = ann.get("columns", [])
            try:
                span_idx = columns.index("gene_span_kb")
            except ValueError:
                span_idx = 0
            for j, g in enumerate(ctx.genes):
                vals = genes_ann.get(g)
                if vals is None:
                    continue
                try:
                    v = vals[span_idx]
                except (IndexError, TypeError):
                    continue
                if v is None:
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv):
                    span[j] = fv

        # Replace non-finite spans with 0
        span = np.where(np.isfinite(span), span, 0.0)

        out = np.zeros((n_perts, n_genes, 1), dtype=np.float64)
        add_f = np.where(np.isfinite(add), add, 0.0)
        out[:, :, 0] = add_f * span[None, :]
        out = np.where(np.isfinite(out), out, 0.0)
        return out
