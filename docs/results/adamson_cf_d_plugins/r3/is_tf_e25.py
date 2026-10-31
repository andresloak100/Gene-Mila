import numpy as np
from genemila.features.api import Feature, register

@register
class IsTfE25(Feature):
    name = "is_tf_e25"
    version = 1
    description = "Binary indicator: 1 if gene g is a transcription factor, else 0."
    rationale = ("Transcription factors may have distinct response patterns due to their "
                 "central role in gene regulation.")
    inputs = ["transcription_factors"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        tf_list = ctx.knowledge("transcription_factors")
        if tf_list:
            tf_set = set(tf_list)
            idx = [ctx.gene_index[g] for g in tf_set if g in ctx.gene_index]
            if idx:
                out[:, idx, 0] = 1.0
        return out
