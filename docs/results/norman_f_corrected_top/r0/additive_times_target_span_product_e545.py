import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveTimesTargetSpanProductE545(Feature):
    name = "additive_times_target_span_product_e545"
    version = 1
    description = ("Elementwise product of additive_response and the product of "
                   "gene_span_kb over all targets of p.")
    rationale = ("Larger target genes may have broader chromatin effects under CRISPRa; "
                 "combining with additive response may refine magnitude.")
    inputs = ["gene_annotation", "additive_response"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=np.float64)

        # additive_response from the composition API
        add = ctx.feature("additive_response", perts)
        if add.ndim == 2:
            add = add[:, :, None]

        # gene span lookup
        ann = ctx.knowledge("gene_annotation")
        span = np.zeros(n_genes, dtype=np.float64)
        if ann is not None:
            genes_map = ann.get("genes", {})
            columns = ann.get("columns", [])
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
        # replace non-finite / non-positive spans with 1.0 so product is well-defined
        bad = ~np.isfinite(span) | (span <= 0)
        span[bad] = 1.0

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            prod = 1.0
            if tgenes:
                for g in tgenes:
                    gi = ctx.gene_index.get(g)
                    if gi is not None:
                        prod *= span[gi]
            out[i, :, 0] = add[i, :, 0] * prod

        out[~np.isfinite(out)] = 0.0
        return out
