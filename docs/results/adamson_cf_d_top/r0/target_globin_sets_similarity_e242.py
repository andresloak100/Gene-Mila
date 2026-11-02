import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGlobinSetsSimilarityE242(Feature):
    name = "target_globin_sets_similarity_e242"
    version = 1
    description = "Jaccard similarity between the target gene's gene-set memberships and the union of globin-gene gene sets, broadcast to all genes."
    rationale = "Targets functionally related to globin genes may perturb globin expression through shared regulatory pathways."
    inputs = ["gene_sets"]
    params = {}
    dim = 1

    GLOBIN_GENES = ("HBZ", "HBA1", "HBG1", "HBG2", "HBM")

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))

        gs = ctx.knowledge("gene_sets")
        if not isinstance(gs, dict):
            return out

        # Build gene -> set of gene-set names
        gene_sets = {}
        for set_name, members in gs.items():
            if not isinstance(members, (list, tuple)):
                continue
            for g in members:
                gene_sets.setdefault(g, set()).add(set_name)

        globin_union = set()
        for g in self.GLOBIN_GENES:
            globin_union |= gene_sets.get(g, set())
        if not globin_union:
            return out

        cache = ctx.cache.setdefault("e242_jaccard", {})
        for i, p in enumerate(perts):
            if p in cache:
                val = cache[p]
            else:
                targets = ctx.target_genes(p)
                best = 0.0
                for t in targets:
                    ts = gene_sets.get(t, set())
                    if not ts:
                        continue
                    inter = len(ts & globin_union)
                    union = len(ts | globin_union)
                    j = inter / union if union > 0 else 0.0
                    if j > best:
                        best = j
                val = best
                cache[p] = val
            out[i, :, 0] = val

        return out
