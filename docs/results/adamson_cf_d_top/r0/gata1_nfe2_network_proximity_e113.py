import numpy as np
from collections import deque
from genemila.features.api import Feature, register


@register
class Gata1Nfe2NetworkProximity(Feature):
    name = "gata1_nfe2_network_proximity_e113"
    version = 1
    description = ("Minimum unweighted graph distance from gene g to GATA1 or NFE2 "
                   "in the prior_network; 0 if g is GATA1/NFE2, max_distance if unreachable.")
    rationale = ("Genes close to erythroid transcription factors GATA1/NFE2 in the prior "
                 "network may be co-regulated and show larger perturbation responses.")
    inputs = ["prior_network"]
    params = {"max_distance": 100}
    dim = 1

    def compute(self, ctx, perts, params):
        max_distance = int(params.get("max_distance", 100))
        n_genes = ctx.n_genes

        # Build gene -> column mapping helper
        gene_index = ctx.gene_index

        # Cache graph structure across perturbations
        cache = ctx.cache
        key = "gata1_nfe2_graph"
        if key not in cache:
            prior = ctx.knowledge("prior_network")
            adj = {}
            if prior:
                for edge in prior:
                    try:
                        a, b = edge[0], edge[1]
                    except Exception:
                        continue
                    if a is None or b is None:
                        continue
                    adj.setdefault(a, set()).add(b)
                    adj.setdefault(b, set()).add(a)
            cache[key] = adj
        adj = cache[key]

        # Multi-source BFS from GATA1 and NFE2
        dist_key = "gata1_nfe2_dist"
        if dist_key not in cache:
            dist = {}
            frontier = deque()
            for seed in ("GATA1", "NFE2"):
                if seed in adj or seed in gene_index:
                    if seed not in dist:
                        dist[seed] = 0
                        frontier.append(seed)
            while frontier:
                node = frontier.popleft()
                d = dist[node]
                if d >= max_distance:
                    continue
                for nb in adj.get(node, ()):
                    if nb not in dist:
                        dist[nb] = d + 1
                        frontier.append(nb)
            cache[dist_key] = dist
        dist = cache[dist_key]

        # Build per-gene distance vector
        gene_dist = np.full(n_genes, float(max_distance), dtype=float)
        for g, idx in gene_index.items():
            if g in dist:
                gene_dist[idx] = float(min(dist[g], max_distance))

        # Same for every perturbation row
        out = np.empty((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = gene_dist[None, :]
        out = np.nan_to_num(out, nan=float(max_distance),
                            posinf=float(max_distance),
                            neginf=float(max_distance))
        return out
