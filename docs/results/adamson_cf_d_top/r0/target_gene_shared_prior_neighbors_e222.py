import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGeneSharedPriorNeighborsE222(Feature):
    name = "target_gene_shared_prior_neighbors_e222"
    version = 1
    description = "Number of common neighbors between target of perturbation p and gene g in prior_network."
    rationale = ("Shared prior network neighbors indicate common regulatory or physical "
                 "interaction partners, so perturbing one gene may affect the other through "
                 "the shared partner.")
    inputs = ["prior_network"]
    params = {"weight_threshold": 0.0}
    dim = 1

    def compute(self, ctx, perts, params):
        thr = float(params.get("weight_threshold", 0.0))
        net = ctx.knowledge("prior_network")

        # Build adjacency sets over gene symbols
        adj = {}
        if net:
            # net may be a list of edges or a dict of {gene: {neighbor: weight}}
            if isinstance(net, dict):
                for a, nbrs in net.items():
                    if isinstance(nbrs, dict):
                        for b, w in nbrs.items():
                            try:
                                w = float(w)
                            except (TypeError, ValueError):
                                continue
                            if not (w > thr):
                                continue
                            adj.setdefault(a, set()).add(b)
                            adj.setdefault(b, set()).add(a)
                    elif isinstance(nbrs, (list, tuple, set)):
                        for b in nbrs:
                            adj.setdefault(a, set()).add(b)
                            adj.setdefault(b, set()).add(a)
            else:
                for edge in net:
                    if len(edge) < 2:
                        continue
                    a, b = edge[0], edge[1]
                    if len(edge) >= 3:
                        try:
                            w = float(edge[2])
                        except (TypeError, ValueError):
                            w = 1.0
                        if not (w > thr):
                            continue
                    adj.setdefault(a, set()).add(b)
                    adj.setdefault(b, set()).add(a)

        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        gene_nbrs = [adj.get(g) for g in ctx.genes]

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            tset = set()
            for t in tgenes:
                s = adj.get(t)
                if s:
                    tset.update(s)
            if not tset:
                # fall back to a non-constant signal: perturbed targets themselves
                tset = set(tgenes)
            if not tset:
                continue
            for j in range(n_genes):
                gn = gene_nbrs[j]
                if not gn:
                    continue
                if len(gn) < len(tset):
                    cnt = sum(1 for x in gn if x in tset)
                else:
                    cnt = sum(1 for x in tset if x in gn)
                out[i, j, 0] = float(cnt)

        # Ensure non-constant: if all zeros, use target identity indicator
        if not np.any(out):
            for i, p in enumerate(perts):
                for j in ctx.target_indices(p):
                    out[i, j, 0] = 1.0

        return out
