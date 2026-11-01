import numpy as np
from genemila.features.api import Feature, register


@register
class CO2TransportMembershipE22(Feature):
    name = "co2_transport_membership_e22"
    version = 1
    description = "Binary indicator: 1 if gene g is in GOBP:carbon dioxide transport, else 0."
    rationale = ("Globin/CO2 transport genes are coordinately regulated and respond distinctly "
                 "to perturbations affecting mitochondrial translation or tRNA charging.")
    inputs = ["gene_sets"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        gs = ctx.knowledge("gene_sets")
        members = set()
        if isinstance(gs, dict):
            key = "GOBP:carbon dioxide transport"
            genes = gs.get(key)
            if genes is None:
                # try case-insensitive / whitespace-tolerant lookup
                for k, v in gs.items():
                    if isinstance(k, str) and k.strip().lower() == key.lower():
                        genes = v
                        break
            if genes:
                members = set(genes)
        if not members:
            return out
        idx = [ctx.gene_index[g] for g in members if g in ctx.gene_index]
        if idx:
            out[:, idx, 0] = 1.0
        return out
