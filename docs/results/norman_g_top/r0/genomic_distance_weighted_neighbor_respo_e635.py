import numpy as np
from genemila.features.api import Feature, register


@register
class GenomicDistanceWeightedNeighborRespo(Feature):
    name = "genomic_distance_weighted_neighbor_respo_e635"
    version = 1
    description = (
        "For gene g, weighted average (1/(distance+offset)) of response-similarity "
        "to its genomic neighbours within 100kb."
    )
    rationale = (
        "Genes close on the chromosome may share regulatory elements; weighting "
        "similarity by inverse genomic distance captures local co-regulation."
    )
    inputs = ["train_delta", "knowledge"]
    params = {"max_distance_kb": 100, "offset_kb": 1}
    dim = 1

    def _build_neighbors(self, ctx, params):
        max_dist = float(params.get("max_distance_kb", 100)) * 1000.0
        kn = ctx.knowledge("gene_annotation")
        neigh_map = {}
        if kn and isinstance(kn, dict):
            neigh_map = kn.get("neighbours", {}) or {}
        gene_index = ctx.gene_index
        n_genes = ctx.n_genes
        # For each gene column, list of (neighbor_col, distance_bp)
        nb = [[] for _ in range(n_genes)]
        for g, gidx in gene_index.items():
            entries = neigh_map.get(g)
            if not entries:
                continue
            for item in entries:
                try:
                    nname, dist = item[0], float(item[1])
                except Exception:
                    continue
                if nname == g:
                    continue
                nidx = gene_index.get(nname)
                if nidx is None:
                    continue
                if dist <= 0:
                    dist = 1.0
                if dist <= max_dist:
                    nb[gidx].append((nidx, dist))
        return nb

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        offset = float(params.get("offset_kb", 1)) * 1000.0

        nb = self._build_neighbors(ctx, params)

        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            d = np.asarray(d, dtype=float)
            n_train = d.shape[0]
            if n_train < 2:
                continue
            # centre and normalise columns for fast correlation
            dmean = d.mean(axis=0)
            dc = d - dmean
            norms = np.sqrt((dc * dc).sum(axis=0))
            safe = norms > 1e-12
            normed = np.zeros_like(dc)
            normed[:, safe] = dc[:, safe] / norms[safe]
            corr = normed.T @ normed  # (n_genes, n_genes)

            col = np.zeros(n_genes, dtype=float)
            for g in range(n_genes):
                nbrs = nb[g]
                if not nbrs:
                    continue
                wsum = 0.0
                vsum = 0.0
                for (nidx, dist) in nbrs:
                    if not safe[g] or not safe[nidx]:
                        continue
                    w = 1.0 / (dist + offset)
                    vsum += w * corr[g, nidx]
                    wsum += w
                if wsum > 0:
                    col[g] = vsum / wsum
            out[i, :, 0] = col

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
