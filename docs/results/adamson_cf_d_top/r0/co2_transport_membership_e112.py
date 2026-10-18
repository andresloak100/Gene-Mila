import numpy as np
from genemila.features.api import Feature, register

@register
class Co2TransportMembership(Feature):
    name = "co2_transport_membership_e112"
    version = 1
    description = "Binary indicator: 1 if gene g is in GOBP:carbon dioxide transport gene set, else 0."
    rationale = ("Genes involved in carbon dioxide transport (including globins) may be "
                 "co-regulated and show coordinated expression changes under perturbations.")
    inputs = ["gene_sets"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        gs = ctx.knowledge("gene_sets")
        members = set()
        if isinstance(gs, dict):
            members = gs.get("GOBP:carbon dioxide transport", []) or []
        member_set = set(members)
        idx = [ctx.gene_index[g] for g in ctx.genes if g in member_set]
        if idx:
            out[:, idx, 0] = 1.0
        return out
