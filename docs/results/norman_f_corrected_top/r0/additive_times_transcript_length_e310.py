import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveTimesTranscriptLengthE310(Feature):
    name = "additive_times_transcript_length_e310"
    version = 1
    description = "Elementwise product of additive_response and the transcript length (from gene_annotation) of gene g."
    rationale = "Longer transcripts may be more sensitive to CRISPRa activation, so scaling the additive baseline by transcript length can improve predictions."
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        ann = ctx.knowledge("gene_annotation")

        # Build transcript length vector aligned to ctx.genes
        tl = np.zeros(n_genes, dtype=float)
        if ann is not None:
            cols = ann.get("columns", [])
            genes_map = ann.get("genes", {})
            try:
                idx = cols.index("transcript_length")
            except ValueError:
                idx = None
            if idx is not None:
                for g, vals in genes_map.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None or vals is None:
                        continue
                    v = vals[idx]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        tl[gi] = fv

        # additive_response via composition (leakage-safe handled by that feature)
        add = ctx.feature("additive_response", perts, params=None)
        add = np.asarray(add, dtype=float)
        if add.ndim == 2:
            add = add[:, :, None]

        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        n = min(add.shape[0], len(perts))
        for i in range(n):
            col = add[i, :, 0]
            prod = col * tl
            prod = np.where(np.isfinite(prod), prod, 0.0)
            out[i, :, 0] = prod
        return out
