import numpy as np
from genemila.features.api import Feature, register

@register
class AdditiveTimesBidirectionalPartner(Feature):
    name = "additive_times_bidirectional_partner_e469"
    version = 1
    description = "Elementwise product of additive_response and a binary indicator of whether gene g has a bidirectional promoter partner."
    rationale = "Bidirectional promoters may cause CRISPRa to affect both genes; this interaction captures that effect."
    inputs = ["knowledge", "feature"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        # Binary indicator: 1 if gene has a bidirectional partner, else 0
        bidir = ctx.knowledge("gene_annotation")
        indicator = np.zeros(n_genes, dtype=np.float64)
        if bidir is not None:
            bd = bidir.get("bidirectional", {})
            for i, g in enumerate(ctx.genes):
                partners = bd.get(g)
                if partners:
                    indicator[i] = 1.0

        # additive_response feature: shape (n_perts, n_genes, dim)
        add = ctx.feature("additive_response", perts)
        if add.ndim == 3:
            add = add[:, :, 0]
        elif add.ndim == 2:
            pass
        else:
            add = add.reshape(len(perts), n_genes)

        out = np.zeros((len(perts), n_genes, 1), dtype=np.float64)
        out[:, :, 0] = add * indicator[None, :]
        return out
