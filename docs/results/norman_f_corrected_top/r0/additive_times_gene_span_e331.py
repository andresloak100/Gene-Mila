import numpy as np
from genemila.features.api import Feature, register

@register
class AdditiveTimesGeneSpan(Feature):
    name = "additive_times_gene_span_e331"
    version = 1
    description = "Elementwise product of additive_response and gene_span_kb of gene g."
    rationale = "Gene span correlates with transcriptional complexity and may modify the magnitude of response."
    inputs = ["additive_response", "gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1), dtype=float)

        # gene_span_kb for every gene in ctx.genes order
        span = np.zeros(ctx.n_genes, dtype=float)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None and isinstance(ann, dict):
            genes_map = ann.get("genes")
            if isinstance(genes_map, dict):
                for i, g in enumerate(ctx.genes):
                    vals = genes_map.get(g)
                    if vals is not None:
                        try:
                            v = float(vals[0])
                            if np.isfinite(v):
                                span[i] = v
                        except (TypeError, ValueError, IndexError):
                            pass

        # additive_response feature: (n, n_genes, 1)
        add = ctx.feature("additive_response", perts, params=None)
        add = np.asarray(add, dtype=float)
        if add.ndim == 2:
            add = add[:, :, None]

        out = add * span[None, :, None]
        out = np.where(np.isfinite(out), out, 0.0)
        return out
