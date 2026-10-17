import numpy as np
from genemila.features.api import Feature, register

@register
class PairTargetCompartmentSimilarityE431(Feature):
    name = "pair_target_compartment_similarity_e431"
    version = 1
    description = "Jaccard similarity of subcellular compartment sets of pair targets (protein_annotation)."
    rationale = ("Proteins in the same compartment may act synergistically/redundantly, while "
                 "different compartments may affect distinct pathways; Jaccard captures overlap.")
    inputs = ["protein_annotation"]
    params = {"single_gene_value": 0.0}
    dim = 1

    # compartment flag columns in protein_annotation
    COMPARTMENTS = ["secreted", "membrane", "endoplasmic_reticulum", "golgi",
                    "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome"]

    def _comp_vectors(self, ctx):
        cache = ctx.cache
        if "e431_comp" in cache:
            return cache["e431_comp"]
        ann = ctx.knowledge("protein_annotation")
        vectors = {}
        if ann is not None:
            cols = ann.get("columns", [])
            genes_tbl = ann.get("genes", {})
            # map compartment name -> column index
            idx = {}
            for c in self.COMPARTMENTS:
                if c in cols:
                    idx[c] = cols.index(c)
            comp_cols = [idx[c] for c in self.COMPARTMENTS if c in idx]
            for g, vals in genes_tbl.items():
                if vals is None:
                    continue
                vec = np.zeros(len(self.COMPARTMENTS), dtype=float)
                for j, c in enumerate(self.COMPARTMENTS):
                    if c in idx:
                        v = vals[idx[c]]
                        if v is not None:
                            try:
                                vec[j] = 1.0 if float(v) > 0.5 else 0.0
                            except (TypeError, ValueError):
                                vec[j] = 0.0
                vectors[g] = vec
        cache["e431_comp"] = vectors
        return vectors

    def compute(self, ctx, perts, params):
        single_val = float(params.get("single_gene_value", 0.0))
        vectors = self._comp_vectors(ctx)
        out = np.full((len(perts), ctx.n_genes, 1), np.nan, dtype=float)

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            if tgenes is None or len(tgenes) != 2:
                val = single_val
            else:
                g1, g2 = tgenes[0], tgenes[1]
                v1 = vectors.get(g1)
                v2 = vectors.get(g2)
                if v1 is None or v2 is None:
                    val = single_val
                else:
                    inter = np.sum(np.minimum(v1, v2))
                    union = np.sum(np.maximum(v1, v2))
                    if union <= 0:
                        val = single_val
                    else:
                        val = float(inter / union)
            out[i, :, 0] = val

        # ensure finite
        out = np.nan_to_num(out, nan=single_val, posinf=single_val, neginf=single_val)
        return out
