import numpy as np
from genemila.features.api import Feature, register


@register
class ReplogleAdditiveXMeanTargetGeneSpanE337(Feature):
    name = "replogle_additive_x_mean_target_gene_spa_e337"
    version = 1
    description = "Product of sign-corrected Replogle additive response and mean gene_span_kb of target genes."
    rationale = ("Larger target genes (gene span) may be more responsive to CRISPRa; "
                 "combining the Replogle-derived target effect with mean target gene span "
                 "captures this heterogeneity.")
    inputs = ["replogle_additive_response_signed_e104", "gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1))

        # Replogle additive response (sign-corrected) for all perturbations
        repl = ctx.feature("replogle_additive_response_signed_e104", perts)
        if repl.ndim == 3:
            repl = repl[:, :, 0]
        elif repl.ndim == 1:
            repl = repl.reshape(n, -1)

        # Gene span from annotation
        ann = ctx.knowledge("gene_annotation")
        spans = None
        if ann is not None and isinstance(ann, dict):
            genes_ann = ann.get("genes")
            cols = ann.get("columns")
            if genes_ann is not None and cols is not None and "gene_span_kb" in cols:
                span_idx = cols.index("gene_span_kb")
                spans = np.full(ctx.n_genes, np.nan)
                for g, gi in ctx.gene_index.items():
                    vals = genes_ann.get(g)
                    if vals is not None and len(vals) > span_idx and vals[span_idx] is not None:
                        try:
                            spans[gi] = float(vals[span_idx])
                        except (TypeError, ValueError):
                            pass

        if spans is None:
            spans = np.zeros(ctx.n_genes)

        # Mean gene span per perturbation (over its target genes)
        mean_span = np.zeros(n)
        for i, p in enumerate(perts):
            idxs = ctx.target_indices(p)
            if len(idxs) == 0:
                mean_span[i] = 0.0
            else:
                vals = spans[idxs]
                vals = vals[np.isfinite(vals)]
                mean_span[i] = float(vals.mean()) if vals.size > 0 else 0.0

        out[:, :, 0] = repl * mean_span[:, None]
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
