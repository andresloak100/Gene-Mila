import numpy as np
from genemila.features.api import Feature, register

@register
class ProteinLocalizationSimilarity(Feature):
    name = "protein_localization_similarity_e251"
    version = 1
    description = "Jaccard similarity between localization flags of the target(s) of p and gene g."
    rationale = "Proteins in the same subcellular compartment may interact or respond together."
    inputs = ["knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        ann = ctx.knowledge("protein_annotation")
        if ann is None:
            return out
        cols = ann.get("columns", [])
        genes = ann.get("genes", {})
        # localization flag columns (0/1)
        loc_cols = ["secreted", "membrane", "endoplasmic_reticulum", "golgi",
                    "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome"]
        col_idx = []
        for c in loc_cols:
            if c in cols:
                col_idx.append(cols.index(c))
        if not col_idx:
            return out
        col_idx = np.array(col_idx, dtype=int)

        # build boolean localization matrix (n_genes x n_flags)
        n_flags = len(col_idx)
        loc = np.zeros((ctx.n_genes, n_flags), dtype=bool)
        for gi, g in enumerate(ctx.genes):
            vals = genes.get(g)
            if vals is None:
                continue
            for j, ci in enumerate(col_idx):
                v = vals[ci]
                if v is not None and not (isinstance(v, float) and np.isnan(v)):
                    try:
                        loc[gi, j] = bool(float(v) > 0.5)
                    except (TypeError, ValueError):
                        pass

        counts = loc.sum(axis=1).astype(float)  # number of flags per gene

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            tgt_idx = [ctx.gene_index[g] for g in tg if g in ctx.gene_index]
            if not tgt_idx:
                continue
            # union of localization flags over targets
            union = loc[tgt_idx].any(axis=0)
            union_count = float(union.sum())
            if union_count == 0:
                continue
            # intersection of union with each gene's flags
            inter = (loc & union[None, :]).sum(axis=1).astype(float)
            union_sizes = union_count + counts - inter
            with np.errstate(invalid="ignore", divide="ignore"):
                jac = np.where(union_sizes > 0, inter / union_sizes, 0.0)
            out[i, :, 0] = jac
        return out
