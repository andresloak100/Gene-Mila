import numpy as np
from genemila.features.api import Feature, register

@register
class GeneInCO2Transport(Feature):
    name = "gene_in_co2_transport_e212"
    version = 1
    description = "Binary indicator: 1 if gene g is in GOBP:carbon dioxide transport gene set."
    rationale = "CO2 transport genes form a co-regulated module that responds to perturbations."
    inputs = ["gene_sets"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        indicator = np.zeros(n_genes, dtype=float)
        gs = ctx.knowledge("gene_sets")
        if isinstance(gs, dict):
            members = gs.get("GOBP:carbon dioxide transport", [])
            for g in members:
                idx = ctx.gene_index.get(g)
                if idx is not None:
                    indicator[idx] = 1.0
        out = np.broadcast_to(indicator[None, :, None], (len(perts), n_genes, 1)).copy()
        return out
