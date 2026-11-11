import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGGeneSetJaccardE239(Feature):
    name = "target_g_gene_set_jaccard_e239"
    version = 1
    description = "Jaccard similarity between gene set memberships of perturbation target and response gene g."
    rationale = "Shared gene set membership indicates functional similarity, so perturbing such targets should affect the response gene more."
    inputs = ["gene_sets"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        n_genes = ctx.n_genes
        out = np.zeros((n_perts, n_genes, 1), dtype=float)

        gs = ctx.knowledge("gene_sets")
        if not gs:
            return out

        # Build mapping gene -> set of gene set ids
        gene_to_sets = {}
        for set_id, members in gs.items():
            if not isinstance(members, (list, tuple)):
                continue
            for m in members:
                if m in ctx.gene_index:
                    gene_to_sets.setdefault(m, set()).add(set_id)

        # Precompute per-gene set membership
        gene_sets_list = [None] * n_genes
        for gname, sidx in ctx.gene_index.items():
            s = gene_to_sets.get(gname)
            if s:
                gene_sets_list[sidx] = s

        cache = ctx.cache
        key = "e239_target_sets"
        target_sets_cache = cache.get(key)
        if target_sets_cache is None:
            target_sets_cache = {}
            for p in ctx.perts:
                tset = set()
                for t in ctx.target_genes(p):
                    s = gene_to_sets.get(t)
                    if s:
                        tset |= s
                target_sets_cache[p] = tset
            cache[key] = target_sets_cache

        for i, p in enumerate(perts):
            tset = target_sets_cache.get(p, set())
            if not tset:
                continue
            n_t = len(tset)
            for g_idx in range(n_genes):
                gset = gene_sets_list[g_idx]
                if not gset:
                    continue
                inter = len(tset & gset)
                if inter == 0:
                    continue
                union = n_t + len(gset) - inter
                if union > 0:
                    out[i, g_idx, 0] = inter / union

        return out
