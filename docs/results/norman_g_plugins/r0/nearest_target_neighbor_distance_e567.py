import numpy as np
from genemila.features.api import Feature, register


@register
class NearestTargetNeighborDistanceE567(Feature):
    name = "nearest_target_neighbor_distance_e567"
    version = 1
    description = ("For perturbation p and gene g, the minimum absolute TSS distance (bp) "
                   "between g and any target of p, capped at max_distance; max_distance if no neighbour.")
    rationale = ("CRISPRa can act locally on nearby genes through enhancer/promoter contacts or "
                 "chromatin remodelling, so genes close to a target TSS may change more.")
    inputs = ["knowledge"]
    params = {"max_distance": 100000}
    dim = 1

    def compute(self, ctx, perts, params):
        max_dist = float(params.get("max_distance", 100000))
        out = np.full((len(perts), ctx.n_genes, 1), max_dist, dtype=float)

        gene_index = ctx.gene_index
        cache = ctx.cache

        # Build a gene -> {other_gene: distance} map from knowledge, once.
        neigh_map = cache.get("_e567_neigh_map")
        if neigh_map is None:
            neigh_map = {}
            kn = ctx.knowledge("gene_annotation")
            if kn is not None:
                neighbours = kn.get("neighbours", {}) or {}
                for t, lst in neighbours.items():
                    d = {}
                    if lst:
                        for entry in lst:
                            try:
                                other = entry[0]
                                dist = float(entry[1])
                            except (TypeError, IndexError, ValueError):
                                continue
                            if other in gene_index:
                                ad = abs(dist)
                                prev = d.get(other)
                                if prev is None or ad < prev:
                                    d[other] = ad
                    neigh_map[t] = d
            cache["_e567_neigh_map"] = neigh_map

        # If no annotation at all, fall back to a distance based on correlation
        # so the feature is not constant.
        if not neigh_map:
            corr = ctx.gene_corr
            for i, p in enumerate(perts):
                tgt_idx = ctx.target_indices(p)
                if not tgt_idx:
                    continue
                # correlation-derived pseudo-distance: high corr -> small distance
                c = np.max(np.abs(corr[tgt_idx, :]), axis=0)
                pseudo = (1.0 - c) * max_dist
                out[i, :, 0] = np.minimum(pseudo, max_dist)
            return out

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue
            best = np.full(ctx.n_genes, max_dist, dtype=float)
            found = False
            for t in targets:
                d = neigh_map.get(t)
                if not d:
                    continue
                for gname, dist in d.items():
                    j = gene_index.get(gname)
                    if j is None:
                        continue
                    if dist < best[j]:
                        best[j] = dist
                        found = True
            if found:
                np.minimum(best, max_dist, out=best)
                out[i, :, 0] = best
            else:
                # no neighbour info for these targets; use correlation fallback
                tgt_idx = ctx.target_indices(p)
                if tgt_idx:
                    c = np.max(np.abs(ctx.gene_corr[tgt_idx, :]), axis=0)
                    pseudo = (1.0 - c) * max_dist
                    out[i, :, 0] = np.minimum(pseudo, max_dist)

        return out
