import numpy as np
from genemila.features.api import Feature, register


@register
class LoeufWeightedPpiNeighborMeanDelta(Feature):
    name = "loeuf_weighted_ppi_neighbor_mean_delta_e_e554"
    version = 1
    description = ("For each (p,g): weighted average of the mean training delta of direct PPI "
                   "neighbors of gene g, with weights = (1 - LOEUF_neighbor).")
    rationale = ("PPI neighbors with low LOEUF (high essentiality) are likely critical hubs; "
                 "their response to perturbation may propagate more strongly to gene g.")
    inputs = ["train_delta", "knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # --- Build LOEUF vector over ctx genes ---
        loeuf = np.full(n_genes, np.nan, dtype=float)
        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            cols = kc.get("columns", [])
            try:
                idx_loeuf = cols.index("oe_lof_upper")
            except ValueError:
                idx_loeuf = None
            genes_map = kc.get("genes", {}) or {}
            if idx_loeuf is not None:
                for g, vals in genes_map.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None:
                        continue
                    try:
                        v = vals[idx_loeuf]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        loeuf[gi] = fv
        # handle missing -> median
        finite_mask = np.isfinite(loeuf)
        if finite_mask.any():
            med = float(np.median(loeuf[finite_mask]))
        else:
            med = 1.0
        loeuf = np.where(finite_mask, loeuf, med)
        weight = 1.0 - loeuf  # (1 - LOEUF)

        # --- Build PPI adjacency (neighbor lists) ---
        ppi = ctx.knowledge("ppi_network")
        neighbors = [[] for _ in range(n_genes)]
        if ppi is not None:
            for entry in ppi:
                try:
                    a, b = entry[0], entry[1]
                except (IndexError, TypeError):
                    continue
                ia = ctx.gene_index.get(a)
                ib = ctx.gene_index.get(b)
                if ia is None or ib is None:
                    continue
                neighbors[ia].append(ib)
                neighbors[ib].append(ia)

        # Precompute per-gene weighted neighbor index arrays and normalized weights
        # (independent of perturbation)
        cache = ctx.cache
        key = "_loeuf_ppi_neighbor_cache_e554"
        if key not in cache:
            nb_idx = []
            nb_w = []
            for g in range(n_genes):
                nbs = neighbors[g]
                if not nbs:
                    nb_idx.append(np.empty(0, dtype=np.int64))
                    nb_w.append(np.empty(0, dtype=float))
                    continue
                arr = np.asarray(nbs, dtype=np.int64)
                w = weight[arr]
                w = np.where(np.isfinite(w), w, 0.0)
                s = w.sum()
                if s > 0:
                    w = w / s
                nb_idx.append(arr)
                nb_w.append(w)
            cache[key] = (nb_idx, nb_w)
        else:
            nb_idx, nb_w = cache[key]

        # --- For each perturbation, compute mean training delta then weighted neighbor mean ---
        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            mean_delta = d.mean(axis=0) if d.shape[0] > 0 else np.zeros(n_genes, dtype=float)
            col = np.zeros(n_genes, dtype=float)
            for g in range(n_genes):
                idx = nb_idx[g]
                if idx.size == 0:
                    continue
                col[g] = float(np.dot(nb_w[g], mean_delta[idx]))
            out[i, :, 0] = col

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
