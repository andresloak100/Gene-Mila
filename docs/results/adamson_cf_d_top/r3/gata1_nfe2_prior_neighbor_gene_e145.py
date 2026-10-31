import numpy as np
from genemila.features.api import Feature, register


@register
class Gata1Nfe2PriorNeighborGeneE145(Feature):
    name = "gata1_nfe2_prior_neighbor_gene_e145"
    version = 1
    description = "Binary: gene g is a neighbor of GATA1 or NFE2 in the prior_network."
    rationale = (
        "Genes regulated by erythroid/mitochondrial transcription factors GATA1 and NFE2 "
        "are co-regulated and show coordinated expression changes."
    )
    inputs = ["prior_network"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        net = ctx.knowledge("prior_network")
        neighbor_mask = np.zeros(n_genes, dtype=float)

        if net:
            targets = {"GATA1", "NFE2"}
            neighbors = set()
            for edge in net:
                if len(edge) < 2:
                    continue
                a, b = edge[0], edge[1]
                if a in targets and b not in targets:
                    neighbors.add(b)
                elif b in targets and a not in targets:
                    neighbors.add(a)

            for g in neighbors:
                idx = ctx.gene_index.get(g)
                if idx is not None:
                    neighbor_mask[idx] = 1.0

        out[:, :, 0] = neighbor_mask[None, :]
        return out
