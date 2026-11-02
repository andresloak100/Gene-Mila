import numpy as np
from genemila.features.api import Feature, register


@register
class Gata1Nfe2NetworkProximityE21(Feature):
    name = "gata1_nfe2_network_proximity_e21"
    version = 1
    description = "Minimum path distance from gene g to GATA1 or NFE2 in prior_network (0 if g is one of them; large constant if disconnected)."
    rationale = "Genes in the GATA1/NFE2 regulatory neighborhood share coordinated responses to perturbations affecting translation or proteostasis."
    inputs = ["prior_network"]
    params = {"max_distance": 5}
    dim = 1

    def compute(self, ctx, perts, params):
        max_distance = float(params.get("max_distance", 5))
        n_genes = ctx.n_genes

        # Default: disconnected -> large constant (normalized value 1.0)
        dist_norm = np.ones(n_genes, dtype=float)

        key = ("gata1_nfe2_proximity", max_distance)
        if key in ctx.cache:
            dist_norm = ctx.cache[key]
        else:
            prior = ctx.knowledge("prior_network")
            if prior is not None:
                # Build gene universe: all genes mentioned in prior_network
                gene_to_local = {}
                edges = []
                for entry in prior:
                    if len(entry) < 2:
                        continue
                    a, b = entry[0], entry[1]
                    if a not in gene_to_local:
                        gene_to_local[a] = len(gene_to_local)
                    if b not in gene_to_local:
                        gene_to_local[b] = len(gene_to_local)
                    edges.append((gene_to_local[a], gene_to_local[b]))
                n_local = len(gene_to_local)

                if n_local > 0:
                    # Build undirected adjacency list
                    adj = [[] for _ in range(n_local)]
                    for a, b in edges:
                        if a != b:
                            adj[a].append(b)
                            adj[b].append(a)

                    # Sources: GATA1, NFE2 (if present)
                    sources = [gene_to_local[g] for g in ("GATA1", "NFE2")
                               if g in gene_to_local]

                    # BFS multi-source
                    INF = np.iinfo(np.int32).max
                    dist = np.full(n_local, INF, dtype=np.int64)
                    from collections import deque
                    dq = deque()
                    for s in sources:
                        dist[s] = 0
                        dq.append(s)
                    while dq:
                        u = dq.popleft()
                        du = dist[u]
                        # cap BFS at max_distance (inclusive distance)
                        if du >= int(max_distance):
                            continue
                        for v in adj[u]:
                            if dist[v] == INF:
                                dist[v] = du + 1
                                dq.append(v)

                    # Map back to ctx gene space
                    for g, li in gene_to_local.items():
                        gi = ctx.gene_index.get(g)
                        if gi is None:
                            continue
                        d = dist[li]
                        if d == INF:
                            dist_norm[gi] = 1.0
                        else:
                            # distance 0 -> 0.0, distance max_distance -> 1.0
                            dist_norm[gi] = min(float(d) / max_distance, 1.0)

            ctx.cache[key] = dist_norm

        # Gene-side feature, broadcast across perturbations
        out = np.empty((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = dist_norm[None, :]
        return out
