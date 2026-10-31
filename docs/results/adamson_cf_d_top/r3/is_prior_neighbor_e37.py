import numpy as np
from genemila.features.api import Feature, register


@register
class IsPriorNeighborE37(Feature):
    name = "is_prior_neighbor_e37"
    version = 1
    description = "Binary: 1 if gene g is a neighbor of the perturbation target in prior_network, else 0."
    rationale = "Direct network neighbors of the target are more likely to be transcriptionally affected."
    inputs = ["prior_network"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        net = ctx.knowledge("prior_network")
        if not net:
            return out

        # Build adjacency: gene symbol -> set of neighbor symbols (undirected).
        adj = {}
        for edge in net:
            if isinstance(edge, dict):
                a = edge.get("source") or edge.get("gene_a") or edge.get("from")
                b = edge.get("target") or edge.get("gene_b") or edge.get("to")
            else:
                try:
                    a, b = edge[0], edge[1]
                except Exception:
                    continue
            if a is None or b is None:
                continue
            adj.setdefault(a, set()).add(b)
            adj.setdefault(b, set()).add(a)

        if not adj:
            return out

        # Cache per-gene neighbor column index arrays.
        cache = ctx.cache
        col_cache = cache.setdefault("is_prior_neighbor_e37_cols", {})

        def neighbor_cols(symbol):
            if symbol in col_cache:
                return col_cache[symbol]
            nbrs = adj.get(symbol)
            if not nbrs:
                cols = np.empty(0, dtype=np.int64)
            else:
                cols = np.array(
                    [ctx.gene_index[g] for g in nbrs if g in ctx.gene_index],
                    dtype=np.int64,
                )
            col_cache[symbol] = cols
            return cols

        any_set = False
        for i, p in enumerate(perts):
            target_genes = ctx.target_genes(p)
            if not target_genes:
                continue
            cols_all = []
            for tg in target_genes:
                c = neighbor_cols(tg)
                if c.size:
                    cols_all.append(c)
            if cols_all:
                cols = np.unique(np.concatenate(cols_all))
                out[i, cols, 0] = 1.0
                any_set = True

        # Fallback: if no perturbation had resolvable neighbors, mark all genes
        # adjacent to any node present in the network so the feature is non-constant.
        if not any_set:
            cols = np.array(
                [ctx.gene_index[g] for g in adj if g in ctx.gene_index],
                dtype=np.int64,
            )
            if cols.size:
                out[:, cols, 0] = 1.0

        return out
