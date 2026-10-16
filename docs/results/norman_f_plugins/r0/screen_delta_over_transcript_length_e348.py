import numpy as np
from genemila.features.api import Feature, register


@register
class ScreenDeltaOverTranscriptLength(Feature):
    name = "screen_delta_over_transcript_length_e348"
    version = 1
    description = "Elementwise ratio of replogle_delta_signed_e35 to transcript length of gene g."
    rationale = "Normalizing signed Replogle delta by transcript length may reduce gene-size noise."
    inputs = ["knowledge", "feature"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        # transcript length per gene, aligned to ctx.genes
        tlen = np.ones(n_genes, dtype=np.float64)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes_ann = ann.get("genes", {})
            cols = ann.get("columns", [])
            try:
                idx = cols.index("transcript_length")
            except ValueError:
                idx = None
            if idx is not None:
                for g in ctx.genes:
                    vals = genes_ann.get(g)
                    if vals is not None and len(vals) > idx and vals[idx] is not None:
                        v = float(vals[idx])
                        if np.isfinite(v) and v > 0:
                            tlen[ctx.gene_index[g]] = v

        # signed replogle delta feature
        rep = ctx.feature("replogle_delta_signed_e35", perts, None)
        rep = np.asarray(rep, dtype=np.float64)
        if rep.ndim == 2:
            rep = rep[:, :, None]
        rep = rep[:, :, 0]

        # elementwise ratio with safe denominator
        denom = tlen[None, :]
        with np.errstate(divide="ignore", invalid="ignore"):
            out[:, :, 0] = np.where(denom > 0, rep / denom, 0.0)

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
