import numpy as np
from genemila.features.api import Feature, register

@register
class PPINeighborResponseE70(Feature):
    name = "ppi_neighbor_response_e70"
    version = 1
    description = "Confidence-weighted average of training deltas over PPI neighbors of each gene."
    rationale = ("Protein-protein interactions propagate perturbation effects; genes connected "
                 "to responsive genes will also respond, so averaging neighbor deltas by PPI "
                 "confidence captures network-propagated effects.")
    inputs = ["train_delta", "ppi_network"]
    params = {"min_weight": 0.5}
    dim = 1

    def compute(self, ctx, perts, params):
        min_weight = float(params.get("min_weight", 0.5))

        # Build sparse adjacency (weighted) from ppi_network prior knowledge.
        ppi = ctx.knowledge("ppi_network")
        n_genes = ctx.n_genes
        gene_index = ctx.gene_index

        # Collect edges as (i, j, w)
        rows, cols, vals = [], [], []
        if ppi is not None:
            for edge in ppi:
                try:
                    a, b, w = edge[0], edge[1], float(edge[2])
                except (IndexError, TypeError, ValueError):
                    continue
                if w < min_weight:
                    continue
                ia = gene_index.get(a)
                ib = gene_index.get(b)
                if ia is None or ib is None:
                    continue
                rows.append(ia); cols.append(ib); vals.append(w)
                rows.append(ib); cols.append(ia); vals.append(w)

        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        if len(rows) == 0:
            # No usable edges: fall back to zero (finite).
            return out

        rows = np.asarray(rows, dtype=np.int64)
        cols = np.asarray(cols, dtype=np.int64)
        vals = np.asarray(vals, dtype=float)

        # Row-normalized weights: for each target gene g, weights over neighbor genes.
        # We want, for gene g: sum_{n neighbor} w_{g,n} * delta[n] / sum_n w_{g,n}
        denom = np.zeros(n_genes, dtype=float)
        np.add.at(denom, rows, vals)
        # Avoid division by zero
        safe_denom = np.where(denom > 0, denom, 1.0)

        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            # d shape (n_train, n_genes)
            # Weighted sum over neighbors for each gene: for each edge (g <- n) add w * mean_delta[n]
            mean_delta = d.mean(axis=0)  # (n_genes,)
            contrib = vals * mean_delta[cols]  # weighted neighbor means per edge
            agg = np.zeros(n_genes, dtype=float)
            np.add.at(agg, rows, contrib)
            out[i, :, 0] = agg / safe_denom

        return out
