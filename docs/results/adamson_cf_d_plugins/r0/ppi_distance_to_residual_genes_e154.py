import numpy as np
from collections import deque
from genemila.features.api import Feature, register


@register
class PPIDistanceToResidualGenes(Feature):
    name = "ppi_distance_to_residual_genes_e154"
    version = 1
    description = ("Minimum shortest-path distance in the PPI network from gene g to any of the "
                   "residual-driving genes (HBZ, HBG2, HBA1, HBG1, HIST1H1C, HIST1H2BK); "
                   "unreachable genes set to a large constant.")
    rationale = ("Residual component is enriched near globin/histone genes; PPI proximity may "
                 "capture functional coupling beyond co-expression.")
    inputs = ["ppi_network"]
    params = {"max_dist": 10.0}
    dim = 1

    def compute(self, ctx, perts, params):
        max_dist = float(params.get("max_dist", 10.0))
        seeds = ["HBZ", "HBG2", "HBA1", "HBG1", "HIST1H1C", "HIST1H2BK"]

        cache = ctx.cache
        key = "_ppi_dist_e154"
        if key not in cache:
            net = ctx.knowledge("ppi_network")
            adj = {}
            if net:
                for edge in net:
                    try:
                        a, b = edge[0], edge[1]
                    except Exception:
                        continue
                    adj.setdefault(a, set()).add(b)
                    adj.setdefault(b, set()).add(a)

            # multi-source BFS from seeds over the full PPI graph
            dist = {}
            dq = deque()
            for s in seeds:
                if s in adj:
                    dist[s] = 0
                    dq.append(s)
            while dq:
                u = dq.popleft()
                du = dist[u]
                for v in adj.get(u, ()):
                    if v not in dist:
                        dist[v] = du + 1
                        dq.append(v)

            gene_dist = np.full(ctx.n_genes, max_dist, dtype=float)
            for gi, g in enumerate(ctx.genes):
                d = dist.get(g)
                if d is not None:
                    gene_dist[gi] = min(float(d), max_dist)
            cache[key] = gene_dist

        gene_dist = cache[key]
        out = np.empty((len(perts), ctx.n_genes, 1), dtype=float)
        out[:, :, 0] = gene_dist[None, :]
        return out
