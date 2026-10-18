import numpy as np
from genemila.features.api import Feature, register


@register
class Gata1Nfe2RegulonMembershipE115(Feature):
    name = "gata1_nfe2_regulon_membership_e115"
    version = 1
    description = "Binary feature: 1 if gene g is a neighbor of GATA1 or NFE2 in prior_network, else 0."
    rationale = ("GATA1 and NFE2 are erythroid transcription factors; genes neighboring them in the "
                 "prior network may be co-regulated and responsive to stress/lineage perturbation.")
    inputs = ["prior_network"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        net = ctx.knowledge("prior_network")
        if net is None:
            return out

        seeds = {"GATA1", "NFE2"}
        members = set()

        # prior_network is a list of [gene_a, gene_b, weight] entries.
        for entry in net:
            try:
                a, b = entry[0], entry[1]
            except (IndexError, TypeError):
                continue
            if a in seeds and b not in seeds:
                members.add(b)
            if b in seeds and a not in seeds:
                members.add(a)

        idx = [ctx.gene_index[g] for g in members if g in ctx.gene_index]
        if idx:
            out[:, idx, 0] = 1.0

        return out
