import numpy as np
from genemila.features.api import Feature, register

@register
class AdditiveTimesTargetTranscriptLength(Feature):
    name = "additive_times_target_transcript_length_e407"
    version = 1
    description = "Elementwise product of additive_response and the mean transcript length of the perturbation's target gene(s)."
    rationale = "Transcript length may affect mRNA stability or translation efficiency, modulating the perturbation effect."
    inputs = ["train_delta", "gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))
        ann = ctx.knowledge("gene_annotation")
        if ann is None:
            return out
        genes = ann.get("genes", {})
        columns = ann.get("columns", [])
        try:
            tl_idx = columns.index("transcript_length")
        except ValueError:
            return out

        # Precompute transcript length per gene column
        tl = np.full(ctx.n_genes, np.nan, dtype=np.float64)
        for g, col in ctx.gene_index.items():
            vals = genes.get(g)
            if vals is not None and len(vals) > tl_idx:
                v = vals[tl_idx]
                if v is not None:
                    tl[col] = float(v)

        # Precompute additive response via additive baseline for each perturbation
        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            add = d.mean(axis=0)
            tg = ctx.target_genes(p)
            lengths = []
            for g in tg:
                gi = ctx.gene_index.get(g)
                if gi is not None:
                    v = tl[gi]
                    if np.isfinite(v):
                        lengths.append(v)
            if lengths:
                mean_tl = float(np.mean(lengths))
            else:
                mean_tl = 0.0
            out[i, :, 0] = add * mean_tl
        return out
