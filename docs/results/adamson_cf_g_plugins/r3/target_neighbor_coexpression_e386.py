import numpy as np
from genemila.features.api import Feature, register


@register
class TargetNeighborCoexpression(Feature):
    name = "target_neighbor_coexpression_e386"
    version = 1
    description = ("Average Pearson correlation between control expression of gene g and "
                   "control expression of each genomic neighbor (within 100 kb) of the target gene.")
    rationale = ("Genomic neighbors may share regulatory elements; perturbing the target could "
                 "affect neighboring genes' expression, and genes coexpressed with those neighbors "
                 "may also respond.")
    inputs = ["control_cells", "gene_corr", "knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # Load neighbour prior once and cache the gene-index mapping.
        cache = ctx.cache
        key = "e386_neighbor_idx"
        if key not in cache:
            nb = ctx.knowledge("gene_annotation")
            gene_index = ctx.gene_index
            neigh_idx = {}
            if isinstance(nb, dict) and "neighbours" in nb:
                raw = nb["neighbours"]
                if isinstance(raw, dict):
                    for sym, lst in raw.items():
                        gi = gene_index.get(sym)
                        if gi is None:
                            continue
                        idxs = []
                        if lst:
                            for entry in lst:
                                # entry is [gene, tss_distance_bp]
                                if isinstance(entry, (list, tuple)) and len(entry) >= 1:
                                    ngi = gene_index.get(entry[0])
                                else:
                                    ngi = gene_index.get(entry)
                                if ngi is not None:
                                    idxs.append(ngi)
                        neigh_idx[gi] = np.array(idxs, dtype=np.int64)
            cache[key] = neigh_idx
        else:
            neigh_idx = cache[key]

        # Correlation matrix across control cells (cached by context).
        corr = ctx.gene_corr

        for i, p in enumerate(perts):
            tlist = ctx.target_indices(p)
            if not tlist:
                continue
            # Use the first target index (single-gene targets in this data).
            t = tlist[0]
            nbrs = neigh_idx.get(t)
            if nbrs is None or nbrs.size == 0:
                continue
            # corr[g, n] for all genes g and all neighbours n -> average over n.
            sub = corr[:, nbrs]  # (n_genes, n_neighbors)
            vals = sub.mean(axis=1)
            # Guard against non-finite values.
            vals = np.where(np.isfinite(vals), vals, 0.0)
            out[i, :, 0] = vals

        return out
