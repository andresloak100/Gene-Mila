import numpy as np
from collections import deque
from genemila.features.api import Feature, register


@register
class PpiGlobinProximityE54(Feature):
    name = "ppi_globin_proximity_e54"
    version = 1
    description = "Inverse PPI-network shortest-path distance from each gene to the globin module."
    rationale = ("PPI proximity to globin genes captures co-regulation with the globin module "
                 "that is under-predicted by other features.")
    inputs = ["ppi_network"]
    params = {"globin_genes": ["HBZ", "HBG2", "HBA1", "HBG1"], "max_distance": 3}
    dim = 1

    def compute(self, ctx, perts, params):
        globin_genes = params.get("globin_genes", ["HBZ", "HBG2", "HBA1", "HBG1"])
        max_distance = int(params.get("max_distance", 3))

        # Build graph once, memoised in ctx.cache
        cache_key = ("ppi_globin_graph", tuple(globin_genes), max_distance)
        if cache_key not in ctx.cache:
            ppi = ctx.knowledge("ppi_network")
            adj = {}
            if ppi is not None:
                for entry in ppi:
                    if len(entry) < 2:
                        continue
                    a, b = entry[0], entry[1]
                    if a == b:
                        continue
                    adj.setdefault(a, set()).add(b)
                    adj.setdefault(b, set()).add(a)

            # Multi-source BFS from globin genes
            dist = {}
            dq = deque()
            for g in globin_genes:
                if g in adj or g in globin_genes:
                    dist[g] = 0
                    dq.append(g)
            while dq:
                u = dq.popleft()
                du = dist[u]
                if du >= max_distance:
                    continue
                for v in adj.get(u, ()):
                    if v not in dist:
                        dist[v] = du + 1
                        dq.append(v)

            # Map to gene columns
            val = np.zeros(ctx.n_genes, dtype=np.float64)
            for gi, gene in enumerate(ctx.genes):
                d = dist.get(gene)
                if d is not None and d <= max_distance:
                    val[gi] = 1.0 / (1.0 + d)
            ctx.cache[cache_key] = val

        base = ctx.cache[cache_key]
        out = np.empty((len(perts), ctx.n_genes, 1), dtype=np.float64)
        out[:, :, 0] = base[None, :]
        return out
