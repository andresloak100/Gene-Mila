import numpy as np
from genemila.features.api import Feature, register

GLOBIN_GENES = ("HBZ", "HBG2", "HBA1", "HBG1", "HBB")


@register
class TargetGlobinSetSimilarityE39(Feature):
    name = "target_globin_set_similarity_e39"
    version = 1
    description = (
        "Jaccard similarity between the union of gene sets containing the "
        "perturbation target gene(s) and the union of gene sets containing "
        "any globin gene (HBZ, HBG2, HBA1, HBG1, HBB)."
    )
    rationale = (
        "Targets co-regulated with globin genes may trigger similar "
        "transcriptional programs, producing larger responses in globin genes."
    )
    inputs = ["gene_sets"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        out = np.zeros((n_perts, ctx.n_genes, 1), dtype=float)

        gs = ctx.knowledge("gene_sets")
        if not isinstance(gs, dict) or len(gs) == 0:
            return out

        # Build gene -> set of set-names mapping (memoised).
        cache = ctx.cache
        if "_e39_gene_to_sets" not in cache:
            gene_to_sets = {}
            for set_name, genes in gs.items():
                if not isinstance(genes, (list, tuple)):
                    continue
                for g in genes:
                    if not isinstance(g, str):
                        continue
                    gene_to_sets.setdefault(g, set()).add(set_name)
            cache["_e39_gene_to_sets"] = gene_to_sets
        gene_to_sets = cache["_e39_gene_to_sets"]

        # Globin union of sets (memoised).
        if "_e39_globin_union" not in cache:
            globin_union = set()
            for g in GLOBIN_GENES:
                globin_union |= gene_to_sets.get(g, set())
            cache["_e39_globin_union"] = globin_union
        globin_union = cache["_e39_globin_union"]

        if len(globin_union) == 0:
            return out

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            if not tgenes:
                continue
            target_union = set()
            for t in tgenes:
                target_union |= gene_to_sets.get(t, set())
            if len(target_union) == 0:
                continue
            inter = len(target_union & globin_union)
            union = len(target_union | globin_union)
            sim = inter / union if union > 0 else 0.0
            out[i, :, 0] = sim

        return out
