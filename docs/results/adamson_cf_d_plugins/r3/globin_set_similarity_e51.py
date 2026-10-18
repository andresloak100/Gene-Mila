import numpy as np
from genemila.features.api import Feature, register


@register
class GlobinSetSimilarityE51(Feature):
    name = "globin_set_similarity_e51"
    version = 1
    description = ("Jaccard similarity between gene g's gene set memberships and the union "
                   "of gene sets of globin genes (HBZ, HBG2, HBA1, HBG1).")
    rationale = ("Globin genes are co-regulated by GATA1/NFE2; genes sharing their functional "
                 "gene sets may exhibit similar perturbation responses.")
    inputs = ["gene_sets"]
    params = {}
    dim = 1

    GLOBIN_GENES = ("HBZ", "HBG2", "HBA1", "HBG1")

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1), dtype=float)

        gs = ctx.knowledge("gene_sets")
        if not isinstance(gs, dict) or len(gs) == 0:
            return out

        # Build gene -> set of gene-set names. Skip metadata keys.
        gene_sets = {}
        for set_name, members in gs.items():
            if not isinstance(members, (list, tuple)):
                continue
            for g in members:
                if not isinstance(g, str):
                    continue
                s = gene_sets.get(g)
                if s is None:
                    s = set()
                    gene_sets[g] = s
                s.add(set_name)

        # Union of gene sets for globin genes.
        globin_union = set()
        for gg in self.GLOBIN_GENES:
            s = gene_sets.get(gg)
            if s:
                globin_union |= s

        sim = np.zeros(n, dtype=float)
        if len(globin_union) > 0:
            gu = globin_union
            gu_size = len(gu)
            for j, g in enumerate(ctx.genes):
                s = gene_sets.get(g)
                if not s:
                    continue
                inter = len(s & gu)
                if inter == 0:
                    continue
                union = len(s) + gu_size - inter
                if union > 0:
                    sim[j] = inter / union

        out[:, :, 0] = sim[None, :]
        return out
