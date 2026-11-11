import numpy as np
from genemila.features.api import Feature, register


@register
class Atf4Atf6PathwayMembershipE112(Feature):
    name = "atf4_atf6_pathway_membership_e112"
    version = 1
    description = "Binary feature: 1 if gene g belongs to any gene set whose name contains 'ATF4' or 'ATF6', else 0."
    rationale = ("ATF4/ATF6 are master regulators of the integrated stress response and unfolded "
                 "protein response, driving large transcriptional changes.")
    inputs = ["gene_sets"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        vec = np.zeros(n_genes, dtype=float)

        gs = ctx.knowledge("gene_sets")
        if isinstance(gs, dict):
            for key, members in gs.items():
                if not isinstance(key, str):
                    continue
                if ("ATF4" in key) or ("ATF6" in key):
                    if not members:
                        continue
                    for g in members:
                        idx = ctx.gene_index.get(g)
                        if idx is not None:
                            vec[idx] = 1.0

        out = np.broadcast_to(vec[None, :, None], (len(perts), n_genes, 1)).copy()
        return out
