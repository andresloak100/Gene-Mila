import numpy as np
from genemila.features.api import Feature, register

@register
class IsTranscriptionFactorE13(Feature):
    name = "is_transcription_factor_e13"
    version = 1
    description = "Binary feature: 1 if gene g is in the transcription_factors list, else 0."
    rationale = ("Transcription factors are central regulators and may show distinct "
                 "perturbation responses compared to non-TF genes.")
    inputs = ["transcription_factors"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        tf_list = ctx.knowledge("transcription_factors")
        mask = np.zeros(ctx.n_genes, dtype=np.float64)
        if tf_list:
            for g in tf_list:
                idx = ctx.gene_index.get(g)
                if idx is not None:
                    mask[idx] = 1.0
        out = np.broadcast_to(mask[None, :, None],
                              (len(perts), ctx.n_genes, 1)).copy()
        return out
