import numpy as np
from genemila.features.api import Feature, register


@register
class MeanTargetSpanXTargetCoexpressionE323(Feature):
    name = "mean_target_span_x_target_coexpression_e323"
    version = 1
    description = "Product of mean gene span (kb) of p's targets and target_coexpression_e14."
    rationale = "Larger target spans may affect more neighboring genes; coexpression captures functional coupling."
    inputs = ["knowledge", "control_cells"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        ann = ctx.knowledge("gene_annotation")
        genes_ann = ann["genes"] if ann is not None else {}
        columns = ann["columns"] if ann is not None else []
        try:
            span_idx = columns.index("gene_span_kb")
        except (ValueError, AttributeError):
            span_idx = 0

        # Precompute target_coexpression_e14 for all perts once (composition).
        coexp = ctx.feature("target_coexpression_e14", perts)
        coexp = np.asarray(coexp, dtype=float)
        if coexp.ndim == 3:
            coexp = coexp[:, :, 0]

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            spans = []
            for g in tg:
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
                    spans.append(fv)
            if len(spans) == 0:
                mean_span = 0.0
            else:
                mean_span = float(np.mean(spans))
            out[i, :, 0] = mean_span * coexp[i]

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
