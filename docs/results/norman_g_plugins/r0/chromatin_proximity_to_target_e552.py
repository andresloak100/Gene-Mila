import numpy as np
from genemila.features.api import Feature, register


@register
class ChromatinProximityToTarget(Feature):
    name = "chromatin_proximity_to_target_e552"
    version = 1
    description = "Proximity of gene g to perturbation target(s) via bidirectional promoters and TSS distance."
    rationale = ("CRISPRa acts at the promoter; genes sharing bidirectional promoters or close TSS "
                 "are more likely to be co-regulated and co-activated.")
    inputs = ["knowledge", "target_genes", "gene_corr"]
    params = {"distance_scale": 10000.0, "corr_weight": 0.5}
    dim = 1

    def compute(self, ctx, perts, params):
        scale = float(params.get("distance_scale", 10000.0))
        if scale <= 0:
            scale = 10000.0
        cw = float(params.get("corr_weight", 0.5))

        cache = ctx.cache
        key = "_e552_lookups"
        if key not in cache:
            ann = ctx.knowledge("gene_annotation")
            bid_map = {}
            neigh_map = {}
            if isinstance(ann, dict):
                b = ann.get("bidirectional", {}) or {}
                if isinstance(b, dict):
                    for g, lst in b.items():
                        s = set()
                        if isinstance(lst, (list, tuple)):
                            for x in lst:
                                s.add(x)
                        bid_map[g] = s
                nb = ann.get("neighbours", {}) or {}
                if isinstance(nb, dict):
                    for g, lst in nb.items():
                        d = {}
                        if isinstance(lst, (list, tuple)):
                            for item in lst:
                                try:
                                    ng, dist = item[0], item[1]
                                    d[ng] = float(dist)
                                except Exception:
                                    continue
                        neigh_map[g] = d
            cache[key] = (bid_map, neigh_map)

        bid_map, neigh_map = cache[key]

        n_genes = ctx.n_genes
        genes = ctx.genes
        gene_index = ctx.gene_index
        gene_corr = ctx.gene_corr
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # Precompute per-gene bidirectional partner set membership arrays lazily.
        # For each target we build a score vector over all genes.
        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue
            best = np.zeros(n_genes, dtype=float)
            for t in targets:
                if t not in gene_index:
                    continue
                t_idx = gene_index[t]
                t_bid = bid_map.get(t, set())
                t_neigh = neigh_map.get(t, {})

                # Distance-based component over all genes.
                dist_score = np.zeros(n_genes, dtype=float)
                for g_idx in range(n_genes):
                    g = genes[g_idx]
                    if g in t_bid:
                        dist_score[g_idx] = 1.0
                        continue
                    if g in t_neigh:
                        d = abs(t_neigh[g])
                        if d <= 100000.0:
                            dist_score[g_idx] = float(np.exp(-d / scale))
                        continue
                    # reverse direction lookup
                    g_bid = bid_map.get(g)
                    if g_bid is not None and t in g_bid:
                        dist_score[g_idx] = 1.0
                        continue
                    g_neigh = neigh_map.get(g)
                    if g_neigh is not None and t in g_neigh:
                        d = abs(g_neigh[t])
                        if d <= 100000.0:
                            dist_score[g_idx] = float(np.exp(-d / scale))

                # Correlation-based component captures co-regulation / shared regulatory context.
                corr_score = np.abs(gene_corr[:, t_idx])
                corr_score = np.nan_to_num(corr_score, nan=0.0, posinf=0.0, neginf=0.0)

                combined = dist_score + cw * corr_score
                np.maximum(best, combined, out=best)

            out[i, :, 0] = best

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
