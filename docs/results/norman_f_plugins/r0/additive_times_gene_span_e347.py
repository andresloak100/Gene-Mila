import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveTimesGeneSpanE347(Feature):
    name = "additive_times_gene_span_e347"
    version = 1
    description = "Elementwise product of additive_response and gene_span_kb for gene g."
    rationale = ("Larger genes may have more regulatory elements and respond more strongly to "
                 "CRISPRa; scaling the additive baseline by gene span modulates the response by gene size.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes

        # Gene span per gene (in kb), aligned to ctx.genes order.
        ann = ctx.knowledge("gene_annotation")
        span = np.zeros(n_genes, dtype=np.float64)
        if ann is not None:
            genes = ann.get("genes", {})
            columns = ann.get("columns", [])
            try:
                span_idx = columns.index("gene_span_kb")
            except ValueError:
                span_idx = 0
            for gi, g in enumerate(ctx.genes):
                vals = genes.get(g)
                if vals is not None:
                    v = vals[span_idx]
                    if v is not None:
                        span[gi] = float(v)
        span = np.nan_to_num(span, nan=0.0, posinf=0.0, neginf=0.0)

        # Additive baseline prediction, computed from training deltas (leave-one-out).
        additive = np.zeros((len(perts), n_genes), dtype=np.float64)
        for i, p in enumerate(perts):
            for t in ctx.target_indices(p):
                additive[i, t] += 1.0
            _, d = ctx.train_delta(exclude=p)
            if d.shape[0] > 0:
                mean_delta = d.mean(axis=0)
            else:
                mean_delta = np.zeros(n_genes, dtype=np.float64)
            additive[i, :] *= mean_delta

        out = additive * span[None, :]
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out[:, :, None]
