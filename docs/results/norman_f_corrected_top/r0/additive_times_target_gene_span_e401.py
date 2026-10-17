import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveTimesTargetGeneSpanE401(Feature):
    name = "additive_times_target_gene_span_e401"
    version = 1
    description = ("Elementwise product of additive_response and the mean gene_span_kb "
                   "of the perturbation's target genes.")
    rationale = ("CRISPRa efficiency may depend on the size of the targeted gene, so the "
                 "additive baseline response is modulated by the target's gene span "
                 "(averaged over the targets of a pair).")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))

        ann = ctx.knowledge("gene_annotation")
        span_map = {}
        if ann is not None:
            genes_ann = ann.get("genes", {})
            columns = ann.get("columns", [])
            try:
                span_idx = columns.index("gene_span_kb")
            except ValueError:
                span_idx = 0
            for sym, vals in genes_ann.items():
                if vals is None:
                    continue
                try:
                    v = vals[span_idx]
                except (IndexError, TypeError):
                    continue
                if v is None:
                    continue
                span_map[sym] = float(v)

        # additive_response feature (shape (n_perts, n_genes, dim))
        add = ctx.feature("additive_response", perts)
        add = np.asarray(add, dtype=float)
        if add.ndim == 2:
            add = add[:, :, None]
        add = np.nan_to_num(add, nan=0.0, posinf=0.0, neginf=0.0)

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            spans = [span_map[g] for g in targets if g in span_map]
            if len(spans) == 0:
                mean_span = 0.0
            else:
                mean_span = float(np.mean(spans))
            out[i, :, 0] = add[i, :, 0] * mean_span

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
