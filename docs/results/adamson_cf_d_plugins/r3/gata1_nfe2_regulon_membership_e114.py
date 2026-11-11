import numpy as np
from genemila.features.api import Feature, register


@register
class Gata1Nfe2RegulonMembershipE114(Feature):
    name = "gata1_nfe2_regulon_membership_e114"
    version = 1
    description = "Binary feature: 1 if gene g is a neighbor of GATA1 or NFE2 in prior_network, else 0."
    rationale = ("GATA1 and NFE2 are erythroid transcription factors; genes connected to them in "
                 "the prior network may be co-regulated and responsive to stress.")
    inputs = ["prior_network"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        mask = np.zeros(n_genes, dtype=float)

        cached = ctx.cache.get("_gata1_nfe2_neighbors_e114")
        if cached is None:
            net = ctx.knowledge("prior_network")
            targets = {"GATA1", "NFE2"}
            neighbors = set()
            if net:
                for edge in net:
                    try:
                        a, b = edge[0], edge[1]
                    except (TypeError, IndexError):
                        continue
                    if a in targets:
                        neighbors.add(b)
                    if b in targets:
                        neighbors.add(a)
            neighbors.discard("GATA1")
            neighbors.discard("NFE2")
            idx = [ctx.gene_index[g] for g in neighbors if g in ctx.gene_index]
            cached = np.zeros(n_genes, dtype=float)
            if idx:
                cached[np.asarray(idx, dtype=int)] = 1.0
            ctx.cache["_gata1_nfe2_neighbors_e114"] = cached

        mask = cached
        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = mask[None, :]
        return out
