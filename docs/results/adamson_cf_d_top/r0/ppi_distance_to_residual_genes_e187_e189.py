import numpy as np
from genemila.features.api import Feature, FeatureContext, register


@register
class PPIDistanceToResidualGenes(Feature):
    name = "ppi_distance_to_residual_genes_e187_e189"
    version = 1
    description = ("Minimum shortest-path distance in the PPI network from gene g to any "
                   "of the residual genes (HBZ, HBG2, HIST1H1C, HBA1, HBG1, MS4A4A, "
                   "HIST1H2BK, MT-ATP6).")
    rationale = ("Residual genes are enriched in specific network neighborhoods; genes close "
                 "to them may share functional modules and thus respond similarly to "
                 "perturbations.")
    inputs = ["ppi_network"]
    params = {}
    dim = 1

    RESIDUAL_GENES = ["HBZ", "HBG2", "HIST1H1C", "HBA1", "HBG1", "MS4A4A",
                      "HIST1H2BK", "MT-ATP6"]
    UNREACHABLE = 1e6

    def compute(self, ctx: FeatureContext, perts: list[str], params: dict) -> np.ndarray:
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        # Build gene -> index map for ctx genes
        gene_index = ctx.gene_index

        # Load PPI network from knowledge
        ppi = ctx.knowledge("ppi_network")
        if ppi is None:
            out[:, :, 0] = self.UNREACHABLE
            return out

        # Cache the distance vector per gene (same for all perts)
        cache_key = "ppi_dist_to_residual_v1"
        if ctx.cache is not None and cache_key in ctx.cache:
            dist_vec = ctx.cache[cache_key]
        else:
            dist_vec = self._compute_distance_vector(ctx, ppi, gene_index)
            if ctx.cache is not None:
                ctx.cache[cache_key] = dist_vec

        out[:, :, 0] = dist_vec[None, :]
        return out

    def _compute_distance_vector(self, ctx, ppi, gene_index):
        n_genes = ctx.n_genes
        dist_vec = np.full(n_genes, self.UNREACHABLE, dtype=float)

        # Build adjacency list over gene symbols present in ctx
        adj = {}
        for entry in ppi:
            try:
                a, b = entry[0], entry[1]
            except (IndexError, TypeError):
                continue
            if a in gene_index and b in gene_index:
                adj.setdefault(a, []).append(b)
                adj.setdefault(b, []).append(a)

        # For each residual gene present, BFS to all reachable genes
        best = np.full(n_genes, self.UNREACHABLE, dtype=float)
        for rg in self.RESIDUAL_GENES:
            if rg not in gene_index:
                continue
            if rg not in adj and rg not in gene_index:
                continue
            # BFS from rg
            dist = {rg: 0.0}
            frontier = [rg]
            d = 0
            while frontier:
                d += 1
                next_frontier = []
                for node in frontier:
                    for nb in adj.get(node, ()):
                        if nb not in dist:
                            dist[nb] = float(d)
                            next_frontier.append(nb)
                frontier = next_frontier
            # Update best
            for sym, dd in dist.items():
                idx = gene_index.get(sym)
                if idx is not None and dd < best[idx]:
                    best[idx] = dd

        dist_vec[:] = best
        return dist_vec
