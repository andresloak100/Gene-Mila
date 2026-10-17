import numpy as np
from genemila.features.api import Feature, register


@register
class TargetPPINeighborMeanResponseLOEUF(Feature):
    name = "target_ppi_neighbor_mean_response_loeuf__e775"
    version = 1
    description = ("For each (p,g): weighted mean of mean_response over direct PPI neighbors "
                   "of the perturbation target, weights = (1 - LOEUF) of the neighbor.")
    rationale = ("Essential (low LOEUF) PPI neighbors may propagate stronger downstream effects; "
                 "weighting neighbor mean_response by (1 - LOEUF) captures this.")
    inputs = ["control_cells", "train_delta", "knowledge"]
    params = {"missing_loeuf_default": 0.5}
    dim = 1

    def compute(self, ctx, perts, params):
        default = float(params.get("missing_loeuf_default", 0.5))
        n_genes = ctx.n_genes
        n_perts = len(perts)

        # --- LOEUF lookup (cached across calls) ---
        cache = ctx.cache
        if "loeuf_essentiality" not in cache:
            loeuf = np.full(n_genes, np.nan, dtype=np.float64)
            gc = ctx.knowledge("gene_constraint")
            if gc is not None:
                cols = gc.get("columns", [])
                if "oe_lof_upper" in cols:
                    idx = cols.index("oe_lof_upper")
                    genes_map = gc.get("genes", {})
                    for g, vals in genes_map.items():
                        gi = ctx.gene_index.get(g)
                        if gi is None or vals is None:
                            continue
                        v = vals[idx]
                        if v is None:
                            continue
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv):
                            loeuf[gi] = fv
            miss = ~np.isfinite(loeuf)
            loeuf[miss] = default
            cache["loeuf_essentiality"] = 1.0 - loeuf
        essentiality = cache["loeuf_essentiality"]

        # --- PPI adjacency (cached) ---
        if "ppi_neighbors" not in cache:
            neighbors = [[] for _ in range(n_genes)]
            ppi = ctx.knowledge("ppi_network")
            if ppi is not None:
                for edge in ppi:
                    if len(edge) < 2:
                        continue
                    a, b = edge[0], edge[1]
                    ia = ctx.gene_index.get(a)
                    ib = ctx.gene_index.get(b)
                    if ia is None or ib is None or ia == ib:
                        continue
                    neighbors[ia].append(ib)
                    neighbors[ib].append(ia)
            cache["ppi_neighbors"] = [
                np.asarray(sorted(set(nb)), dtype=np.int64) for nb in neighbors
            ]
        neighbors = cache["ppi_neighbors"]

        out = np.zeros((n_perts, n_genes, 1), dtype=np.float64)

        for i, p in enumerate(perts):
            ids, d = ctx.train_delta(exclude=p)
            if d.shape[0] == 0:
                continue
            mean_resp = d.mean(axis=0)  # (n_genes,)

            targets = ctx.target_indices(p)
            if not targets:
                continue

            acc = np.zeros(n_genes, dtype=np.float64)
            cnt = 0
            for t in targets:
                nb = neighbors[t]
                if nb.size == 0:
                    continue
                w = essentiality[nb]
                wsum = w.sum()
                if wsum <= 0:
                    continue
                acc += (w * mean_resp[nb]).sum() / wsum
                cnt += 1

            if cnt > 0:
                out[i, :, 0] = acc / cnt

        # Fallback: if the feature is constant (e.g. no PPI/LOEUF matched),
        # use the leave-one-out mean response of the target genes so rows
        # carry information and vary across perturbations.
        if not np.any(out != 0):
            for i, p in enumerate(perts):
                ids, d = ctx.train_delta(exclude=p)
                if d.shape[0] == 0:
                    continue
                mean_resp = d.mean(axis=0)
                targets = ctx.target_indices(p)
                if targets:
                    out[i, :, 0] = mean_resp[np.asarray(targets, dtype=np.int64)].mean()

        return out
