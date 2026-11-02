import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import shortest_path
from genemila.features.api import Feature, register


@register
class TargetGenePPIShortestPath(Feature):
    name = "target_gene_ppi_shortest_path_e268"
    version = 1
    description = "Shortest path length in the PPI network between the perturbation target and gene g."
    rationale = "Proteins that interact directly or via few intermediates are more likely to influence each other's expression upon perturbation."
    inputs = ["ppi_network"]
    params = {"max_path": 10}
    dim = 1

    def compute(self, ctx, perts, params):
        max_path = float(params.get("max_path", 10))
        n_genes = ctx.n_genes

        cache = ctx.cache
        if "ppi_graph_e268" not in cache:
            net = ctx.knowledge("ppi_network")
            gene_index = ctx.gene_index
            n = n_genes
            rows, cols, data = [], [], []
            if net:
                for edge in net:
                    try:
                        a, b, w = edge[0], edge[1], float(edge[2])
                    except (IndexError, ValueError, TypeError):
                        continue
                    ia = gene_index.get(a)
                    ib = gene_index.get(b)
                    if ia is None or ib is None:
                        continue
                    # weight = inverse confidence so stronger interactions = shorter distance
                    w = max(w, 1e-6)
                    dist = 1.0 / w
                    rows.append(ia); cols.append(ib); data.append(dist)
                    rows.append(ib); cols.append(ia); data.append(dist)
            if rows:
                graph = csr_matrix((data, (rows, cols)), shape=(n, n))
            else:
                graph = csr_matrix((n, n))
            cache["ppi_graph_e268"] = graph

        graph = cache["ppi_graph_e268"]
        n = n_genes

        # Precompute all-pairs shortest paths once (n=2055 is fine for dijkstra; sparse)
        if "ppi_dist_e268" not in cache:
            if graph.nnz == 0:
                cache["ppi_dist_e268"] = None
            else:
                cache["ppi_dist_e268"] = shortest_path(graph, method="D", directed=False)
        dist_matrix = cache["ppi_dist_e268"]

        out = np.full((len(perts), n, 1), max_path, dtype=float)
        if dist_matrix is None:
            return out

        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if not t_idx:
                continue
            t = t_idx[0]
            row = dist_matrix[t]
            # replace inf with max_path, cap at max_path
            r = np.where(np.isfinite(row), row, max_path)
            r = np.minimum(r, max_path)
            out[i, :, 0] = r

        return out
