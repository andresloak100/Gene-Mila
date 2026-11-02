import numpy as np
from genemila.features.api import Feature, register


@register
class PriorNetworkTransferE26(Feature):
    name = "prior_network_transfer_e26"
    version = 1
    description = "Weighted average of mean_response of prior_network neighbors of each gene."
    rationale = "Known functional interactions propagate perturbation responses; neighbor responses provide a prior for gene g."
    inputs = ["prior_network", "train_delta"]
    params = {"use_weights": True}
    dim = 1

    def compute(self, ctx, perts, params):
        use_weights = bool(params.get("use_weights", True))
        n_genes = ctx.n_genes

        # Build adjacency (neighbor index -> weight) from prior_network
        net = ctx.knowledge("prior_network")
        neigh_idx = [[] for _ in range(n_genes)]
        neigh_w = [[] for _ in range(n_genes)]
        if net:
            for entry in net:
                if not entry or len(entry) < 2:
                    continue
                a, b = entry[0], entry[1]
                try:
                    w = float(entry[2]) if len(entry) > 2 else 1.0
                except (TypeError, ValueError):
                    w = 1.0
                if not np.isfinite(w) or w <= 0:
                    w = 1.0
                ia = ctx.gene_index.get(a)
                ib = ctx.gene_index.get(b)
                if ia is None or ib is None:
                    continue
                neigh_idx[ia].append(ib)
                neigh_w[ia].append(w)
                neigh_idx[ib].append(ia)
                neigh_w[ib].append(w)

        # Precompute flattened adjacency for vectorised gather
        has_neigh = np.array([len(x) > 0 for x in neigh_idx], dtype=bool)
        flat_src = np.concatenate(
            [np.full(len(neigh_idx[g]), g, dtype=np.int64) for g in range(n_genes)]
        ) if n_genes > 0 else np.zeros(0, dtype=np.int64)
        flat_dst = np.concatenate(
            [np.asarray(neigh_idx[g], dtype=np.int64) for g in range(n_genes)]
        ) if n_genes > 0 else np.zeros(0, dtype=np.int64)
        if use_weights:
            flat_w = np.concatenate(
                [np.asarray(neigh_w[g], dtype=np.float64) for g in range(n_genes)]
            ) if n_genes > 0 else np.zeros(0, dtype=np.float64)
        else:
            flat_w = np.ones_like(flat_dst, dtype=np.float64)

        # Per-gene weight sums
        wsum = np.zeros(n_genes, dtype=np.float64)
        if flat_src.size > 0:
            np.add.at(wsum, flat_src, flat_w)

        out = np.zeros((len(perts), n_genes, 1), dtype=np.float64)

        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            mr = d.mean(axis=0) if d.shape[0] > 0 else np.zeros(n_genes, dtype=np.float64)
            mr = np.nan_to_num(mr, nan=0.0, posinf=0.0, neginf=0.0)

            vals = np.zeros(n_genes, dtype=np.float64)
            if flat_src.size > 0:
                contrib = flat_w * mr[flat_dst]
                agg = np.zeros(n_genes, dtype=np.float64)
                np.add.at(agg, flat_src, contrib)
                valid = has_neigh & (wsum > 0)
                vals[valid] = agg[valid] / wsum[valid]

            vals = np.nan_to_num(vals, nan=0.0, posinf=0.0, neginf=0.0)
            out[i, :, 0] = vals

        return out
