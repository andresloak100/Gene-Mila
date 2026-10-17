import numpy as np
from genemila.features.api import Feature, register

FLAGS = ["secreted", "membrane", "endoplasmic_reticulum", "golgi",
         "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome"]


@register
class TargetLocalizationSimilarity(Feature):
    name = "target_localization_similarity_e239"
    version = 1
    description = "Jaccard similarity between target gene(s) localization flags and gene g flags."
    rationale = "Perturbations may preferentially affect genes sharing the subcellular compartment of their targets."
    inputs = ["protein_annotation"]
    params = {"pseudocount": 0.0}
    dim = 1

    def compute(self, ctx, perts, params):
        pc = float(params.get("pseudocount", 0.0))
        ann = ctx.knowledge("protein_annotation")

        n_genes = ctx.n_genes
        # Build flag matrix (n_genes, n_flags)
        flag_mat = np.zeros((n_genes, len(FLAGS)), dtype=float)
        if ann is not None:
            cols = ann.get("columns", [])
            genes_tab = ann.get("genes", {})
            col_idx = {}
            for f in FLAGS:
                if f in cols:
                    col_idx[f] = cols.index(f)
            for gi, g in enumerate(ctx.genes):
                vals = genes_tab.get(g)
                if vals is None:
                    continue
                for fi, f in enumerate(FLAGS):
                    if f in col_idx:
                        v = vals[col_idx[f]]
                        if v is not None:
                            try:
                                flag_mat[gi, fi] = 1.0 if float(v) > 0 else 0.0
                            except (TypeError, ValueError):
                                pass

        flag_sums = flag_mat.sum(axis=1)  # (n_genes,)

        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            # union of flags across target genes
            union = flag_mat[tgt_idx].max(axis=0)  # (n_flags,)
            union_sum = float(union.sum())
            # intersection with each gene's flags: union & g
            inter = flag_mat * union[None, :]  # (n_genes, n_flags)
            inter_sum = inter.sum(axis=1)
            denom = union_sum + flag_sums - inter_sum
            jac = np.where(denom > 0, inter_sum / np.maximum(denom, 1e-12), 0.0)
            out[i, :, 0] = jac + pc * 0.0  # pseudocount is additive constant below
            if pc != 0.0:
                out[i, :, 0] = out[i, :, 0] + pc
        return out
