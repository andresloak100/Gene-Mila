import numpy as np
from genemila.features.api import Feature, register

LOC_FLAGS = [
    "secreted", "membrane", "endoplasmic_reticulum", "golgi",
    "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome",
]


@register
class TargetLocalizationOverlapE92(Feature):
    name = "target_localization_overlap_e92"
    version = 1
    description = (
        "Count of shared subcellular localization flags between protein of gene g "
        "and protein(s) of perturbation target(s)."
    )
    rationale = (
        "Proteins in the same compartment are more likely to interact functionally, "
        "so perturbing one may affect others in that compartment."
    )
    inputs = ["protein_annotation"]
    params = {"aggregation": "max"}
    dim = 1

    def _get_flags(self, ctx, gene):
        """Return a boolean vector of localization flags for a gene, or None."""
        ann = ctx.knowledge("protein_annotation")
        if ann is None:
            return None
        genes = ann.get("genes", {})
        cols = ann.get("columns", [])
        if gene not in genes:
            return None
        vals = genes[gene]
        if vals is None:
            return None
        # Map flag columns to indices
        flag = np.zeros(len(LOC_FLAGS), dtype=bool)
        for j, fname in enumerate(LOC_FLAGS):
            if fname in cols:
                idx = cols.index(fname)
                if idx < len(vals) and vals[idx] is not None:
                    try:
                        flag[j] = bool(float(vals[idx]) > 0)
                    except (TypeError, ValueError):
                        flag[j] = False
        return flag

    def compute(self, ctx, perts, params):
        agg = params.get("aggregation", "max")
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        # Precompute gene flags matrix (n_genes, n_flags)
        ann = ctx.knowledge("protein_annotation")
        gene_flags = np.zeros((n_genes, len(LOC_FLAGS)), dtype=bool)
        gene_present = np.zeros(n_genes, dtype=bool)
        if ann is not None:
            genes = ann.get("genes", {})
            cols = ann.get("columns", [])
            flag_col_idx = []
            for fname in LOC_FLAGS:
                if fname in cols:
                    flag_col_idx.append(cols.index(fname))
                else:
                    flag_col_idx.append(-1)
            for gi, g in enumerate(ctx.genes):
                vals = genes.get(g)
                if vals is None:
                    continue
                gene_present[gi] = True
                for j, idx in enumerate(flag_col_idx):
                    if idx >= 0 and idx < len(vals) and vals[idx] is not None:
                        try:
                            gene_flags[gi, j] = float(vals[idx]) > 0
                        except (TypeError, ValueError):
                            pass

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            tflags = []
            for tg in tgenes:
                if tg in ctx.gene_index:
                    gi = ctx.gene_index[tg]
                    if gene_present[gi]:
                        tflags.append(gene_flags[gi])
            if not tflags:
                continue
            tflags = np.array(tflags, dtype=bool)  # (n_targets, n_flags)
            # Intersection size with each gene: (n_genes, n_targets)
            inter = gene_flags.astype(np.int32) @ tflags.astype(np.int32).T
            if agg == "sum":
                out[i, :, 0] = inter.sum(axis=1)
            else:  # max
                out[i, :, 0] = inter.max(axis=1)
        return out
