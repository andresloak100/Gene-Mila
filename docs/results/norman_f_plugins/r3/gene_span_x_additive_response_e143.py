import numpy as np
from genemila.features.api import Feature, register

@register
class GeneSpanXAdditiveResponse(Feature):
    name = "gene_span_x_additive_response_e143"
    version = 1
    description = "Product of gene_span_kb for gene g and additive_response for perturbation p."
    rationale = ("Larger genes may have more regulatory elements or be more susceptible to "
                 "CRISPRa; interacting gene span with the additive baseline prediction may "
                 "capture response dynamics that depend on gene size.")
    inputs = ["gene_annotation", "additive_response"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        span = np.zeros(ctx.n_genes, dtype=float)
        if ann is not None:
            genes_map = ann.get("genes", {}) or {}
            columns = ann.get("columns", []) or []
            try:
                span_idx = columns.index("gene_span_kb")
            except ValueError:
                span_idx = 0
            for g, idx in ctx.gene_index.items():
                vals = genes_map.get(g)
                if vals is not None and span_idx < len(vals):
                    v = vals[span_idx]
                    if v is not None:
                        span[idx] = float(v)

        base = ctx.feature("additive_response", perts, params)
        if base.ndim == 3:
            base = base[:, :, 0]
        elif base.ndim == 1:
            base = base.reshape(-1, ctx.n_genes)

        out[:, :, 0] = base * span[None, :]
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
