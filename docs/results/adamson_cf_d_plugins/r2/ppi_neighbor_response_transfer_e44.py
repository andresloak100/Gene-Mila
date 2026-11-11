import numpy as np
from genemila.features.api import Feature, register


@register
class PPINeighborResponseTransferE44(Feature):
    name = "ppi_neighbor_response_transfer_e44"
    version = 1
    description = (
        "Weighted average of leave-one-out training deltas of each gene's PPI "
        "neighbors, using ppi_network edge weights."
    )
    rationale = (
        "Proteins that physically interact are likely co-regulated or functionally "
        "coupled, so their expression changes after perturbation should be correlated."
    )
    inputs = ["train_delta", "ppi_network"]
    params = {"min_weight": 0.0}
    dim = 1

    def compute(self, ctx, perts, params):
        min_weight = float(params.get("min_weight", 0.0))

        # Build sparse neighbor structure from ppi_network once.
        cache_key = ("ppi_adj_e44", min_weight)
        if cache_key not in ctx.cache:
            n = ctx.n_genes
            # Collect edges
            rows = []
            cols = []
            vals = []
            net = ctx.knowledge("ppi_network") or []
            for edge in net:
                if not edge or len(edge) < 3:
                    continue
                a, b, w = edge[0], edge[1], edge[2]
                try:
                    w = float(w)
                except (TypeError, ValueError):
                    continue
                ia = ctx.gene_index.get(a)
                ib = ctx.gene_index.get(b)
                if ia is None or ib is None:
                    continue
                if w <= min_weight:
                    continue
                if w <= 0:
                    continue
                rows.append(ia); cols.append(ib); vals.append(w)
                rows.append(ib); cols.append(ia); vals.append(w)

            if rows:
                rows = np.asarray(rows, dtype=np.int64)
                cols = np.asarray(cols, dtype=np.int64)
                vals = np.asarray(vals, dtype=np.float64)
                # Build adjacency lists for vectorized weighted mean.
                # Sort by row for grouping.
                order = np.argsort(rows, kind="stable")
                rows = rows[order]
                cols = cols[order]
                vals = vals[order]
                # Row sums for normalization
                row_sum = np.zeros(n, dtype=np.float64)
                np.add.at(row_sum, rows, vals)
                # Indices into edge arrays per gene
                # Use CSR-like offsets
                offsets = np.zeros(n + 1, dtype=np.int64)
                np.add.at(offsets, rows + 1, 1)
                offsets = np.cumsum(offsets)
            else:
                rows = np.zeros(0, dtype=np.int64)
                cols = np.zeros(0, dtype=np.int64)
                vals = np.zeros(0, dtype=np.float64)
                row_sum = np.zeros(n, dtype=np.float64)
                offsets = np.zeros(n + 1, dtype=np.int64)

            ctx.cache[cache_key] = (rows, cols, vals, row_sum, offsets)

        rows, cols, vals, row_sum, offsets = ctx.cache[cache_key]
        n_genes = ctx.n_genes

        out = np.zeros((len(perts), n_genes, 1), dtype=np.float64)

        for i, p in enumerate(perts):
            _, delta = ctx.train_delta(exclude=p)
            # delta shape: (n_train, n_genes)
            if delta.size == 0:
                continue
            # Weighted average over neighbors for each gene:
            # For gene g: sum_{e in edges of g} w_e * delta_mean[neighbor_e] / sum w_e
            # First compute mean delta over training perts per gene.
            mean_delta = delta.mean(axis=0)  # (n_genes,)
            # For each edge, contribution = val * mean_delta[col]
            contrib = vals * mean_delta[cols]
            # Sum contributions per row (gene)
            gene_sum = np.zeros(n_genes, dtype=np.float64)
            np.add.at(gene_sum, rows, contrib)
            # Normalize
            with np.errstate(invalid="ignore", divide="ignore"):
                res = np.where(row_sum > 0, gene_sum / row_sum, 0.0)
            out[i, :, 0] = res

        # Ensure finite
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
