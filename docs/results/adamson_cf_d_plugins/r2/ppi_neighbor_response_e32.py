import numpy as np
from genemila.features.api import Feature, register


@register
class PPINeighborResponseE32(Feature):
    name = "ppi_neighbor_response_e32"
    version = 1
    description = ("Confidence-weighted average of training deltas of PPI network "
                   "neighbors of gene g, leaving out perturbation p.")
    rationale = ("Proteins that physically interact often share functional pathways and "
                 "transcriptional responses; neighbor response transfers this shared signal.")
    inputs = ["train_delta", "ppi_network"]
    params = {"edge_weight_threshold": 0.0}
    dim = 1

    def _build_adjacency(self, ctx, threshold):
        key = ("ppi_adj", float(threshold))
        cache = ctx.cache
        if key in cache:
            return cache[key]

        n_genes = ctx.n_genes
        gi = ctx.gene_index
        ppi = ctx.knowledge("ppi_network")

        rows = []
        cols = []
        vals = []
        if ppi is not None:
            for entry in ppi:
                if len(entry) < 3:
                    continue
                a, b, w = entry[0], entry[1], entry[2]
                if a not in gi or b not in gi:
                    continue
                try:
                    w = float(w)
                except (TypeError, ValueError):
                    continue
                if not np.isfinite(w) or w <= threshold:
                    continue
                ia = gi[a]
                ib = gi[b]
                if ia == ib:
                    continue
                rows.append(ia); cols.append(ib); vals.append(w)
                rows.append(ib); cols.append(ia); vals.append(w)

        if len(rows) == 0:
            adj = np.zeros((n_genes, n_genes), dtype=np.float64)
        else:
            adj = np.zeros((n_genes, n_genes), dtype=np.float64)
            np.add.at(adj, (np.asarray(rows, dtype=np.int64),
                            np.asarray(cols, dtype=np.int64)),
                      np.asarray(vals, dtype=np.float64))

        row_sum = adj.sum(axis=1)
        # Normalize rows; genes without neighbors get all-zero rows.
        norm = np.zeros_like(adj)
        nz = row_sum > 0
        if np.any(nz):
            norm[nz, :] = adj[nz, :] / row_sum[nz, None]

        cache[key] = norm
        return norm

    def compute(self, ctx, perts, params, ):
        threshold = float(params.get("edge_weight_threshold", 0.0))
        adj = self._build_adjacency(ctx, threshold)  # (n_genes, n_genes), row-normalized

        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=np.float64)

        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)  # (n_train, n_genes)
            if d.shape[0] == 0:
                continue
            mean_delta = d.mean(axis=0)  # (n_genes,)
            out[i, :, 0] = adj @ mean_delta

        out[~np.isfinite(out)] = 0.0
        return out
