import numpy as np
from genemila.features.api import Feature, register


@register
class TargetNTranscriptsE39(Feature):
    name = "target_n_transcripts_e39"
    version = 1
    description = "Number of transcripts for the targeted gene, broadcast to all genes."
    rationale = ("Genes with more isoforms may have more complex regulation, leading to "
                 "broader effects when perturbed.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))
        ann = ctx.knowledge("gene_annotation")
        if ann is None:
            return out
        genes = ann.get("genes", {})
        cols = ann.get("columns", [])
        try:
            nt_idx = cols.index("n_transcripts")
        except ValueError:
            return out

        # precompute default (median of available) for missing targets
        vals = []
        for g, v in genes.items():
            if v is None or nt_idx >= len(v):
                continue
            x = v[nt_idx]
            if x is not None:
                vals.append(float(x))
        default = float(np.median(vals)) if vals else 0.0

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            val = default
            for t in tg:
                v = genes.get(t)
                if v is not None and nt_idx < len(v) and v[nt_idx] is not None:
                    val = float(v[nt_idx])
                    break
            out[i, :, 0] = val
        return out
