import numpy as np
from genemila.features.api import Feature, register

@register
class TargetNeighborDistanceE105(Feature):
    name = "target_neighbor_distance_e105"
    version = 1
    description = "For gene g, minimum TSS distance to any target gene of perturbation p, capped at max_distance."
    rationale = "CRISPRa near a target TSS may affect neighbouring genes via enhancer/promoter interactions; distance to target modulates effect size."
    inputs = ["knowledge"]
    params = {"max_distance": 100000}
    dim = 1

    def compute(self, ctx, perts, params):
        max_d = float(params.get("max_distance", 100000))
        out = np.full((len(perts), ctx.n_genes, 1), max_d, dtype=float)

        nb = ctx.knowledge("gene_annotation")
        neighbours = None
        if isinstance(nb, dict):
            neighbours = nb.get("neighbours")

        gene_index = ctx.gene_index

        # Cache per-gene distance maps lazily
        cache = ctx.cache
        dist_cache = cache.setdefault("_tnd_e105_dist", {})

        def dist_map(gene):
            # returns dict gene->distance for neighbours of `gene`, capped
            if gene in dist_cache:
                return dist_cache[gene]
            d = {}
            if neighbours is not None:
                entries = neighbours.get(gene)
                if entries:
                    for item in entries:
                        try:
                            g2 = item[0]
                            dd = float(item[1])
                        except (TypeError, IndexError, ValueError):
                            continue
                        if dd < 0:
                            dd = -dd
                        if g2 in gene_index:
                            d[g2] = dd
            dist_cache[gene] = d
            return d

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue
            # For each target, get its neighbour distance map; take min across targets
            best = np.full(ctx.n_genes, max_d, dtype=float)
            for t in targets:
                # distance to itself is 0
                if t in gene_index:
                    best[gene_index[t]] = 0.0
                dm = dist_map(t)
                for g2, dd in dm.items():
                    j = gene_index[g2]
                    if dd < best[j]:
                        best[j] = dd
            np.minimum(best, max_d, out=best)
            out[i, :, 0] = best

        return out
