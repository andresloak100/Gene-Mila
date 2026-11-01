import numpy as np
from genemila.features.api import Feature, register

@register
class GeneSetOverlapWithTarget(Feature):
    name = "gene_set_overlap_with_target_e143"
    version = 1
    description = "Count/Jaccard of gene sets shared between the perturbation target and gene g."
    rationale = "Shared pathway membership indicates functional coupling, so perturbing one member may affect the other."
    inputs = ["gene_sets"]
    params = {"use_jaccard": 0}
    dim = 1

    def compute(self, ctx, perts, params):
        use_jaccard = int(params.get("use_jaccard", 0))
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        gs = ctx.knowledge("gene_sets")
        if not gs:
            return out

        # Build gene -> list of set ids (only for genes present in ctx)
        gene_sets_of = {}
        for set_name, members in gs.items():
            if not isinstance(members, (list, tuple)):
                continue
            for g in members:
                if g in ctx.gene_index:
                    gene_sets_of.setdefault(g, []).append(set_name)

        # Cache as sets for intersection
        set_cache = {}
        n_genes = ctx.n_genes
        gene_index = ctx.gene_index

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            # Collect union of sets of all target genes
            target_sets = set()
            for t in targets:
                lst = gene_sets_of.get(t)
                if lst:
                    if t not in set_cache:
                        set_cache[t] = set(lst)
                    target_sets |= set_cache[t]
            if not target_sets:
                continue
            tsize = len(target_sets)
            for g, lst in gene_sets_of.items():
                gi = gene_index[g]
                if g not in set_cache:
                    set_cache[g] = set(lst)
                gset = set_cache[g]
                inter = len(target_sets & gset)
                if inter == 0:
                    continue
                if use_jaccard:
                    union = tsize + len(gset) - inter
                    out[i, gi, 0] = inter / union if union > 0 else 0.0
                else:
                    out[i, gi, 0] = float(inter)

        out[~np.isfinite(out)] = 0.0
        return out
