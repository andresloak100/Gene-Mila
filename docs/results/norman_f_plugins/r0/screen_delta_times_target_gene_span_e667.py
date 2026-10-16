import numpy as np
from genemila.features.api import Feature, register


@register
class ScreenDeltaTimesTargetGeneSpanE667(Feature):
    name = "screen_delta_times_target_gene_span_e667"
    version = 1
    description = ("Elementwise product of replogle_delta_signed_e35 and the sum of "
                   "gene_span_kb over all target genes of the perturbation.")
    rationale = ("Larger target genes may have more off-target effects or stronger "
                 "activation due to more sgRNA binding sites; interacting the signed "
                 "screen delta with the summed genomic footprint of the targets may "
                 "improve prediction.")
    inputs = ["replogle_delta_signed_e35", "gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        screen = ctx.feature("replogle_delta_signed_e35", perts, params=None)
        screen = np.asarray(screen, dtype=float)
        if screen.ndim == 2:
            screen = screen[:, :, None]

        ann = ctx.knowledge("gene_annotation")
        span_col = None
        if ann is not None:
            columns = ann.get("columns", [])
            for j, c in enumerate(columns):
                if c == "gene_span_kb":
                    span_col = j
                    break
        genes_map = ann.get("genes", {}) if ann is not None else {}

        cache = ctx.cache
        key = "e667_span"
        span_of = cache.get(key)
        if span_of is None:
            span_of = {}
            if span_col is not None:
                for g, vals in genes_map.items():
                    if vals is None:
                        continue
                    v = vals[span_col]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        span_of[g] = fv
            cache[key] = span_of

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            s = 0.0
            for t in targets:
                v = span_of.get(t)
                if v is not None:
                    s += v
            out[i, :, 0] = screen[i, :, 0] * s
        return out
