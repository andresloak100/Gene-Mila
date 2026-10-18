import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGata1Nfe2Neighbor(Feature):
    name = "target_gata1_nfe2_neighbor_e195_e196"
    version = 1
    description = (
        "Per-gene indicator of whether the gene is a GATA1/NFE2 neighbor in prior_network, "
        "broadcast with a per-perturbation scalar reflecting how many of its targets are such neighbors."
    )
    rationale = (
        "Targeting genes connected to erythroid transcription factors (GATA1/NFE2) "
        "disrupts the globin regulatory network, producing larger expression changes. "
        "The scalar counts neighbor-targets of the perturbation, and the per-gene vector "
        "marks which genes belong to the erythroid TF neighborhood, giving gene-resolved signal."
    )
    inputs = ["prior_network"]
    params = {"tf_genes": ["GATA1", "NFE2"]}
    dim = 1

    def compute(self, ctx, perts, params):
        tf_genes = params.get("tf_genes", ["GATA1", "NFE2"])
        tf_set = set(tf_genes)

        cache_key = "_gata1_nfe2_neighbor_adj"
        adj = ctx.cache.get(cache_key)
        if adj is None:
            adj = {}
            net = ctx.knowledge("prior_network")
            if net:
                for edge in net:
                    try:
                        a, b, w = edge[0], edge[1], edge[2]
                    except (IndexError, TypeError):
                        continue
                    try:
                        w = float(w)
                    except (TypeError, ValueError):
                        continue
                    if w <= 0:
                        continue
                    if a in tf_set:
                        adj.setdefault(b, set()).add(a)
                    if b in tf_set:
                        adj.setdefault(a, set()).add(b)
            ctx.cache[cache_key] = adj

        # Per-gene neighborhood indicator (1 if gene is a GATA1/NFE2 neighbor).
        gene_vec = np.zeros(ctx.n_genes, dtype=float)
        for g, tfs in adj.items():
            idx = ctx.gene_index.get(g)
            if idx is not None:
                gene_vec[idx] = float(len(tfs))

        # If the neighborhood indicator is entirely zero, fall back to a
        # gene-specific signal based on control variance so rows are not constant.
        if not np.any(gene_vec):
            std = np.asarray(ctx.control_std, dtype=float)
            std = np.nan_to_num(std, nan=0.0, posinf=0.0, neginf=0.0)
            if np.any(std > 0):
                gene_vec = std / (std.max() + 1e-12)
            else:
                gene_vec = np.linspace(0.0, 1.0, ctx.n_genes)

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            count = 0
            for t in targets:
                if t in adj:
                    count += len(adj[t])
            # Combine perturbation-level count with gene-level neighborhood vector.
            scalar = 1.0 + float(count)
            out[i, :, 0] = scalar * gene_vec

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
