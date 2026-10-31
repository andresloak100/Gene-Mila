import numpy as np
from genemila.features.api import Feature, register


@register
class PPIErythroidNeighborTransferE56(Feature):
    name = "ppi_erythroid_neighbor_transfer_e56"
    version = 1
    description = ("Similarity-weighted average of training deltas over PPI-network "
                   "neighbors of gene g that are prior_network neighbors of GATA1/NFE2.")
    rationale = ("Erythroid transcriptional program propagates through physical protein "
                 "interactions, so responses of interacting partners carry signal for g.")
    inputs = ["train_delta", "ppi_network", "prior_network"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        gene_index = ctx.gene_index

        # --- Build erythroid-related gene set from prior_network neighbors of GATA1/NFE2 ---
        erythroid = set()
        pn = ctx.knowledge("prior_network")
        if pn is not None:
            if isinstance(pn, dict):
                edges = pn.get("edges", pn.get("network", pn.get("interactions", [])))
            else:
                edges = pn
            for e in edges:
                if not isinstance(e, (list, tuple)) or len(e) < 2:
                    continue
                a, b = e[0], e[1]
                if a in ("GATA1", "NFE2"):
                    erythroid.add(b)
                elif b in ("GATA1", "NFE2"):
                    erythroid.add(a)
        erythroid.discard("GATA1")
        erythroid.discard("NFE2")

        # Map erythroid gene names to column indices
        erythroid_idx = np.array(
            [gene_index[g] for g in erythroid if g in gene_index], dtype=np.int64
        )

        # --- Build PPI adjacency (weighted) restricted to erythroid neighbors ---
        # For each gene g, list of (erythroid neighbor index, weight)
        ppi = ctx.knowledge("ppi_network")
        # Accumulate weighted sums per gene over erythroid partners
        # We store sparse-ish lists per gene.
        nbr_lists = [[] for _ in range(n_genes)]
        if ppi is not None and len(erythroid_idx) > 0:
            erythroid_set = set(erythroid_idx.tolist())
            if isinstance(ppi, dict):
                ppi_edges = ppi.get("edges", ppi.get("network", ppi.get("interactions", [])))
            else:
                ppi_edges = ppi
            for e in ppi_edges:
                if not isinstance(e, (list, tuple)) or len(e) < 2:
                    continue
                a, b = e[0], e[1]
                try:
                    w = float(e[2]) if len(e) > 2 else 1.0
                except (TypeError, ValueError):
                    w = 1.0
                if not np.isfinite(w) or w <= 0:
                    continue
                ia = gene_index.get(a)
                ib = gene_index.get(b)
                if ia is None or ib is None:
                    continue
                # if b is erythroid, contributes to a; if a is erythroid, contributes to b
                if ib in erythroid_set:
                    nbr_lists[ia].append((ib, w))
                if ia in erythroid_set:
                    nbr_lists[ib].append((ia, w))

        # Precompute, for each gene, arrays of neighbor indices and normalized weights
        gene_nbr_idx = [None] * n_genes
        gene_nbr_w = [None] * n_genes
        for g in range(n_genes):
            lst = nbr_lists[g]
            if not lst:
                continue
            idxs = np.array([x[0] for x in lst], dtype=np.int64)
            ws = np.array([x[1] for x in lst], dtype=np.float64)
            s = ws.sum()
            if s <= 0 or not np.isfinite(s):
                continue
            gene_nbr_idx[g] = idxs
            gene_nbr_w[g] = ws / s

        has_nbr = np.array([gene_nbr_idx[g] is not None for g in range(n_genes)])

        out = np.zeros((len(perts), n_genes, 1), dtype=np.float64)

        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)  # (n_train, n_genes)
            if d.shape[0] == 0:
                continue
            # Mean delta per gene over training perturbations (fallback baseline)
            mean_d = d.mean(axis=0)
            out[i, :, 0] = mean_d

            if not has_nbr.any():
                continue

            # Weighted transfer from erythroid PPI neighbors
            for g in np.nonzero(has_nbr)[0]:
                idxs = gene_nbr_idx[g]
                ws = gene_nbr_w[g]
                vals = mean_d[idxs]
                out[i, g, 0] = float(np.dot(ws, vals))

        return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
