import numpy as np
from genemila.features.api import Feature, register

@register
class TFNeighborInteractionE171(Feature):
    name = "tf_neighbor_interaction_e171"
    version = 1
    description = "Interaction between is_tf_neighbor (prior_network neighbors of GATA1/NFE2/ATF4) and mean_response."
    rationale = ("Genes regulated by GATA1, NFE2, or ATF4 may respond coordinately to perturbations; "
                 "scaling the generic response by a neighbor indicator captures baseline responsiveness.")
    inputs = ["prior_network", "train_delta"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = len(perts)
        G = ctx.n_genes
        out = np.zeros((n, G, 1), dtype=float)

        # Build binary indicator: gene g is a neighbor of GATA1/NFE2/ATF4 in prior_network
        tfs = {"GATA1", "NFE2", "ATF4"}
        is_neighbor = np.zeros(G, dtype=float)
        net = ctx.knowledge("prior_network")
        if net:
            pairs = set()
            for edge in net:
                try:
                    a, b = edge[0], edge[1]
                except (TypeError, IndexError):
                    continue
                pairs.add((a, b))
                pairs.add((b, a))
            for tf in tfs:
                if tf not in ctx.gene_index:
                    continue
                for (a, b) in pairs:
                    if a == tf:
                        j = ctx.gene_index.get(b)
                        if j is not None:
                            is_neighbor[j] = 1.0

        # Mean response per perturbation (leave-one-out)
        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            mr = d.mean(axis=0)
            out[i, :, 0] = is_neighbor * mr

        return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
