import numpy as np
from genemila.features.api import Feature, register

LOC_FLAGS = ["secreted", "membrane", "endoplasmic_reticulum", "golgi",
             "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome"]


@register
class ProteinLocalizationSimilarity(Feature):
    name = "protein_localization_similarity_e475"
    version = 1
    description = "Jaccard similarity between localization flags of gene g and the union of flags of p's targets."
    rationale = "Proteins in the same cellular compartments may respond to a perturbation via shared machinery."
    inputs = ["protein_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        ann = ctx.knowledge("protein_annotation")
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        # Build set-of-flags per gene column
        gene_flags = [set() for _ in range(n_genes)]
        if ann is not None:
            genes_tbl = ann.get("genes", {})
            columns = ann.get("columns", [])
            col_idx = {c: i for i, c in enumerate(columns)}
            flag_cols = [(f, col_idx[f]) for f in LOC_FLAGS if f in col_idx]
            for g, col in ctx.gene_index.items():
                vals = genes_tbl.get(g)
                if vals is None:
                    continue
                s = set()
                for fname, fi in flag_cols:
                    v = vals[fi]
                    if v is not None and v == 1:
                        s.add(fname)
                gene_flags[col] = s

        # Target flag unions per perturbation
        target_union = []
        for p in perts:
            u = set()
            for ti in ctx.target_indices(p):
                u |= gene_flags[ti]
            target_union.append(u)

        for i in range(len(perts)):
            u = target_union[i]
            if not u:
                continue
            for g in range(n_genes):
                sg = gene_flags[g]
                if not sg:
                    continue
                inter = len(sg & u)
                if inter == 0:
                    continue
                union = len(sg | u)
                out[i, g, 0] = inter / union

        return out
