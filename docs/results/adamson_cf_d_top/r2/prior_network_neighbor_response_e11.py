import numpy as np
from genemila.features.api import Feature, register

@register
class PriorNetworkNeighborResponseE11(Feature):
    name = "prior_network_neighbor_response_e11"
    version = 1
    description = ("Weighted average of training deltas over a gene's neighbors in the "
                   "prior_network, using edge confidence as weights.")
    rationale = ("Known regulatory interactions imply that perturbing a gene may propagate "
                 "to its network neighbors; averaging neighbor responses captures this propagation.")
    inputs = ["train_delta", "prior_network"]
    params = {"min_weight": 0.5}
    dim = 1

    def compute(self, ctx, perts, params):
        min_weight = float(params.get("min_weight", 0.5))
        n_genes = ctx.n_genes
        gene_index = ctx.gene_index

        # Build weighted adjacency (symmetric) from prior_network edges.
        adj = np.zeros((n_genes, n_genes), dtype=np.float64)
        net = ctx.knowledge("prior_network")
        if net:
            for edge in net:
                try:
                    a, b, w = edge[0], edge[1], float(edge[2])
                except (IndexError, TypeError, ValueError):
                    continue
                if w < min_weight:
                    continue
                ia = gene_index.get(a)
                ib = gene_index.get(b)
                if ia is None or ib is None:
                    continue
                if ia == ib:
                    continue
                # keep max weight if duplicate edges
                if w > adj[ia, ib]:
                    adj[ia, ib] = w
                    adj[ib, ia] = w

        out = np.zeros((len(perts), n_genes, 1), dtype=np.float64)

        # Cache the neighbor weight sums (row sums) since adjacency is fixed.
        wsum = adj.sum(axis=1)  # (n_genes,)

        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)  # (n_train, n_genes)
            if d.shape[0] == 0:
                continue
            mean_delta = d.mean(axis=0)  # (n_genes,)
            # For each gene g: sum_h adj[g,h] * mean_delta[h] / sum_h adj[g,h]
            numer = adj @ mean_delta  # (n_genes,)
            vals = np.zeros(n_genes, dtype=np.float64)
            nz = wsum > 0
            vals[nz] = numer[nz] / wsum[nz]
            out[i, :, 0] = vals

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
