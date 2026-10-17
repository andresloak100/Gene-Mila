import numpy as np
from genemila.features.api import Feature, register

COMPARTMENTS = ["secreted", "membrane", "endoplasmic_reticulum", "golgi",
                "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome"]


@register
class ProteinLocalizationSimilarityE484(Feature):
    name = "protein_localization_similarity_e484"
    version = 1
    description = "Jaccard similarity between gene g's protein compartment set and the union of p's target proteins' compartment sets."
    rationale = "Genes whose protein products localize to the same cellular compartment as the perturbation target are more likely to respond."
    inputs = ["knowledge", "target_genes"]
    params = {"min_compartments": 1}
    dim = 1

    def _gene_sets(self, ctx):
        cache = ctx.cache
        key = "_e484_loc_sets"
        if key in cache:
            return cache[key]
        ann = ctx.knowledge("protein_annotation")
        sets = {}
        if ann is not None:
            genes = ann.get("genes", {})
            cols = ann.get("columns", [])
            idx = {}
            for c in COMPARTMENTS:
                if c in cols:
                    idx[c] = cols.index(c)
            for g, vals in genes.items():
                if vals is None:
                    continue
                s = set()
                for c, ci in idx.items():
                    try:
                        v = vals[ci]
                    except (IndexError, TypeError):
                        continue
                    if v is not None and v == 1:
                        s.add(c)
                sets[g] = s
        cache[key] = sets
        return sets

    def compute(self, ctx, perts, params):
        min_comp = int(params.get("min_compartments", 1))
        sets = self._gene_sets(ctx)
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        # Per-gene compartment sets aligned to columns
        gene_sets = []
        for g in ctx.genes:
            s = sets.get(g, set())
            gene_sets.append(s)

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            union = set()
            for t in tg:
                union |= sets.get(t, set())
            if len(union) < min_comp:
                continue
            nu = len(union)
            for j in range(n_genes):
                gs = gene_sets[j]
                if not gs:
                    continue
                inter = len(gs & union)
                if inter == 0:
                    continue
                denom = len(gs) + nu - inter
                if denom > 0:
                    out[i, j, 0] = inter / denom
        return out
