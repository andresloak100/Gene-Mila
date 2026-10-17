import numpy as np
from genemila.features.api import Feature, register

@register
class SharedCompartmentSimilarityE559(Feature):
    name = "shared_compartment_similarity_e559"
    version = 1
    description = ("Cosine similarity between binary protein-compartment flag vectors "
                   "of the perturbation target and each gene.")
    rationale = ("Proteins localizing to the same cellular compartment as the target "
                 "may be functionally coupled, so their expression changes more.")
    inputs = ["protein_annotation", "target_genes"]
    params = {"missing_value": "0"}
    dim = 1

    COMPARTMENTS = ["secreted", "membrane", "endoplasmic_reticulum", "golgi",
                    "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome"]

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        ann = ctx.knowledge("protein_annotation")
        if ann is None:
            return out

        genes_map = ann.get("genes", {})
        columns = ann.get("columns", [])

        # Locate compartment flag columns
        col_idx = []
        for comp in self.COMPARTMENTS:
            if comp in columns:
                col_idx.append(columns.index(comp))
            else:
                col_idx.append(-1)

        n_comp = len(self.COMPARTMENTS)

        # Build gene x compartment matrix aligned to ctx.genes
        flags = np.zeros((n_genes, n_comp), dtype=float)
        for gi, gene in enumerate(ctx.genes):
            vals = genes_map.get(gene)
            if vals is None:
                continue
            for ci, idx in enumerate(col_idx):
                if idx < 0 or idx >= len(vals):
                    continue
                v = vals[idx]
                if v is None:
                    continue
                try:
                    flags[gi, ci] = 1.0 if float(v) > 0.5 else 0.0
                except (TypeError, ValueError):
                    pass

        # Precompute norms
        norms = np.sqrt((flags * flags).sum(axis=1))  # (n_genes,)

        for i, p in enumerate(perts):
            tgt_genes = ctx.target_genes(p)
            tgt_vec = np.zeros(n_comp, dtype=float)
            found = False
            for tg in tgt_genes:
                gi = ctx.gene_index.get(tg)
                if gi is not None:
                    tgt_vec = np.maximum(tgt_vec, flags[gi])
                    found = True
            if not found:
                continue
            tgt_norm = np.sqrt((tgt_vec * tgt_vec).sum())
            if tgt_norm == 0.0:
                continue
            dots = flags @ tgt_vec  # (n_genes,)
            denom = norms * tgt_norm
            sim = np.zeros(n_genes, dtype=float)
            valid = denom > 0
            sim[valid] = dots[valid] / denom[valid]
            out[i, :, 0] = sim

        return out
