import numpy as np
from genemila.features.api import Feature, register


@register
class Gata1Nfe2RegulonMembership(Feature):
    name = "gata1_nfe2_regulon_membership_e83"
    version = 1
    description = "Binary feature: 1 if gene g is a neighbor of GATA1 or NFE2 in the prior_network, else 0."
    rationale = ("Genes in the GATA1/NFE2 erythroid regulon are coordinately regulated and show "
                 "larger perturbation responses, explaining part of the shared residual pattern.")
    inputs = ["prior_network"]
    params = {"network": "prior_network", "regulators": ["GATA1", "NFE2"], "weight_threshold": 0.0}
    dim = 1

    def compute(self, ctx, perts, params):
        net_name = params.get("network", "prior_network")
        regulators = params.get("regulators", ["GATA1", "NFE2"])
        thr = float(params.get("weight_threshold", 0.0))

        net = ctx.knowledge(net_name)
        reg_set = set(regulators)
        members = set()
        if net:
            for edge in net:
                try:
                    a, b, w = edge[0], edge[1], float(edge[2])
                except (TypeError, ValueError, IndexError):
                    continue
                if w <= thr:
                    continue
                if a in reg_set:
                    members.add(b)
                if b in reg_set:
                    members.add(a)

        vec = np.zeros(ctx.n_genes, dtype=float)
        for g in members:
            idx = ctx.gene_index.get(g)
            if idx is not None:
                vec[idx] = 1.0

        out = np.empty((len(perts), ctx.n_genes, 1), dtype=float)
        out[:, :, 0] = vec[None, :]
        return out
