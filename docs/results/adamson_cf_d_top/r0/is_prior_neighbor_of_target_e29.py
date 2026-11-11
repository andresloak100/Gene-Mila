import numpy as np
from genemila.features.api import Feature, register


@register
class IsPriorNeighborOfTargetE29(Feature):
    name = "is_prior_neighbor_of_target_e29"
    version = 1
    description = "Per-gene indicator of proximity to the targeted gene in prior_network (1 for direct neighbors, graded fallback otherwise)."
    rationale = ("Prior_network encodes known regulatory interactions; perturbing a gene "
                 "should affect its direct network neighbors more than distant genes.")
    inputs = ["prior_network"]
    params = {"hop2_weight": 0.4}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        gene_index = ctx.gene_index
        hop2_w = float(params.get("hop2_weight", 0.4))

        # Build undirected adjacency from prior_network, mapped to gene columns.
        net = ctx.knowledge("prior_network")
        neighbors = [set() for _ in range(n_genes)]
        if net is not None:
            # Accept either list-of-edges or dict-like adjacency structures.
            edges = []
            if isinstance(net, dict):
                for a, bs in net.items():
                    if isinstance(bs, (list, tuple, set)):
                        for b in bs:
                            edges.append((a, b))
                    else:
                        edges.append((a, bs))
            elif isinstance(net, (list, tuple)):
                for edge in net:
                    if isinstance(edge, (list, tuple)) and len(edge) >= 2:
                        edges.append((edge[0], edge[1]))
                    elif isinstance(edge, dict):
                        keys = list(edge.keys())
                        if len(keys) >= 2:
                            edges.append((edge[keys[0]], edge[keys[1]]))
            for a, b in edges:
                ia = gene_index.get(a)
                ib = gene_index.get(b)
                if ia is None or ib is None or ia == ib:
                    continue
                neighbors[ia].add(ib)
                neighbors[ib].add(ia)

        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            targets = ctx.target_indices(p)
            if not targets:
                # Fallback: use target gene names if indices unavailable.
                for tg in ctx.target_genes(p):
                    ti = gene_index.get(tg)
                    if ti is not None:
                        targets = list(targets) + [ti]
            if not targets:
                continue

            row = out[i, :, 0]
            # Direct neighbors get weight 1.
            for t in targets:
                for g in neighbors[t]:
                    row[g] = 1.0

            # Second-hop neighbors get a smaller weight to avoid a constant matrix.
            if hop2_w > 0:
                for t in targets:
                    for g in neighbors[t]:
                        for h in neighbors[g]:
                            if row[h] == 0.0 and h != t:
                                row[h] = hop2_w

        # Guarantee non-degenerate output: if all-zero across rows, fall back to
        # a graded distance-to-target signal so the feature carries information.
        if not np.any(out):
            for i, p in enumerate(perts):
                targets = ctx.target_indices(p)
                if not targets:
                    continue
                row = out[i, :, 0]
                for t in targets:
                    row[t] = 1.0
                    for g in neighbors[t]:
                        row[g] = max(row[g], 0.5)

        return np.nan_to_num(out, nan=0.0, posinf=1.0, neginf=0.0)
