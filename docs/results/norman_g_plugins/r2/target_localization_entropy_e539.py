import numpy as np
from genemila.features.api import Feature, register

@register
class TargetLocalizationEntropy(Feature):
    name = "target_localization_entropy_e539"
    version = 1
    description = "Shannon entropy of subcellular localization flags across p's target genes (protein_annotation)."
    rationale = "Diverse localizations among targets may indicate broader downstream effects; entropy captures this diversity."
    inputs = ["protein_annotation"]
    params = {}
    dim = 1

    # Localization flag columns in protein_annotation
    FLAGS = [
        "secreted", "membrane", "endoplasmic_reticulum", "golgi",
        "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome",
    ]

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))
        ann = ctx.knowledge("protein_annotation")
        if ann is None:
            return out
        columns = ann.get("columns", [])
        genes = ann.get("genes", {})
        # indices of flag columns
        flag_idx = []
        for f in self.FLAGS:
            if f in columns:
                flag_idx.append(columns.index(f))
        if not flag_idx:
            return out
        flag_idx = np.array(flag_idx, dtype=int)

        # Precompute per-gene flag vector (counts as 0/1 across flag categories)
        cache = ctx.cache
        key = "_loc_flag_matrix"
        if key not in cache:
            mat = np.zeros((ctx.n_genes, len(flag_idx)), dtype=np.float64)
            for gi, g in enumerate(ctx.genes):
                vals = genes.get(g)
                if vals is None:
                    continue
                for j, ci in enumerate(flag_idx):
                    v = vals[ci]
                    if v is not None:
                        try:
                            mat[gi, j] = float(v)
                        except (TypeError, ValueError):
                            pass
            cache[key] = mat
        mat = cache[key]

        for i, p in enumerate(perts):
            tgt = ctx.target_indices(p)
            if not tgt:
                continue
            counts = mat[tgt].sum(axis=0)
            total = counts.sum()
            if total <= 0:
                continue
            probs = counts / total
            probs = probs[probs > 0]
            out[i, :, 0] = -np.sum(probs * np.log(probs))
        return out
