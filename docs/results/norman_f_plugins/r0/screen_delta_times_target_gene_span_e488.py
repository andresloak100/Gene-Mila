import numpy as np
from genemila.features.api import Feature, register

@register
class ScreenDeltaTimesTargetGeneSpanE488(Feature):
    name = "screen_delta_times_target_gene_span_e488"
    version = 1
    description = "Signed Replogle screen delta times the sum of gene_span_kb over the perturbation's target genes."
    rationale = ("Gene span correlates with regulatory complexity; multiplying the signed screen "
                 "delta of the target(s) by their gene span may capture how much regulatory "
                 "surface a CRISPRa perturbation of that target can affect.")
    inputs = ["replogle_delta_signed_e35", "gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1))

        # signed screen delta feature (n_perts, n_genes, 1)
        screen = ctx.feature("replogle_delta_signed_e35", perts, params=None)
        screen = np.asarray(screen, dtype=float)
        if screen.ndim == 2:
            screen = screen[:, :, None]

        ann = ctx.knowledge("gene_annotation")
        genes_map = {}
        if ann is not None:
            genes_map = ann.get("genes", {}) or {}

        # gene_span_kb is the first column of the annotation values
        span_cache = {}

        def span_of(g):
            if g in span_cache:
                return span_cache[g]
            v = genes_map.get(g)
            val = 0.0
            if v is not None and len(v) > 0:
                try:
                    x = float(v[0])
                    if np.isfinite(x):
                        val = x
                except (TypeError, ValueError):
                    val = 0.0
            span_cache[g] = val
            return val

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            total = 0.0
            for g in tg:
                total += span_of(g)
            out[i, :, 0] = screen[i, :, 0] * total

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
