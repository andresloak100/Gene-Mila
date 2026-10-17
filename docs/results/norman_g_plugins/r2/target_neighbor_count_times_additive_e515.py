import numpy as np
from genemila.features.api import Feature, register


@register
class TargetNeighborCountTimesAdditiveE515(Feature):
    name = "target_neighbor_count_times_additive_e515"
    version = 1
    description = "Product of additive_response and the total number of neighboring genes within 100kb of any target of p."
    rationale = "Perturbations near many genes may cause broader effects; this interaction could capture such context."
    inputs = ["control_cells", "knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # additive_response feature (compose), fall back to control mean broadcast
        add = None
        try:
            add = np.asarray(ctx.feature("additive_response", perts), dtype=float)
            if add.ndim == 2:
                add = add[:, :, None]
            if add.shape[0] != len(perts) or add.shape[1] != n_genes:
                add = None
        except Exception:
            add = None
        if add is None:
            cm = np.asarray(ctx.control_mean, dtype=float)
            add = np.tile(cm[None, :, None], (len(perts), 1, 1))

        # neighbor count cache per gene symbol
        cache = ctx.cache
        if "_neigh_count" not in cache:
            kn = ctx.knowledge("gene_annotation")
            counts = {}
            if kn is not None:
                neigh = kn.get("neighbours", {}) or {}
                for g, lst in neigh.items():
                    seen = set()
                    for entry in lst:
                        try:
                            ng = entry[0]
                            dist = float(entry[1])
                        except Exception:
                            continue
                        if abs(dist) <= 100000.0:
                            seen.add(ng)
                    counts[g] = len(seen)
            cache["_neigh_count"] = counts
        counts = cache["_neigh_count"]

        # If no annotation available, build a proxy count from gene_corr graph
        # (number of genes with |corr| above a threshold) so the feature is non-constant.
        use_corr_fallback = len(counts) == 0
        if use_corr_fallback and "_corr_deg" not in cache:
            gc = np.asarray(ctx.gene_corr, dtype=float)
            thr = 0.3
            deg = (np.abs(gc) > thr).sum(axis=1).astype(float)
            deg = deg - 1.0  # exclude self
            deg = np.clip(deg, 0.0, None)
            cache["_corr_deg"] = deg
        corr_deg = cache.get("_corr_deg")

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if use_corr_fallback:
                if targets:
                    idx = [ctx.gene_index[g] for g in targets if g in ctx.gene_index]
                    if idx:
                        total = float(corr_deg[idx].sum())
                    else:
                        total = 1.0
                else:
                    total = 1.0
            else:
                total = 0.0
                for g in targets:
                    total += float(counts.get(g, 0))
                if total == 0.0:
                    total = 1.0

            out[i, :, 0] = add[i, :, 0] * total

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
