import numpy as np
from genemila.features.api import Feature, register

_COMPARTMENTS = ["secreted", "membrane", "endoplasmic_reticulum", "golgi",
                 "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome"]


@register
class TargetCompartmentSimilarity(Feature):
    name = "target_compartment_similarity_e121_e135"
    version = 1
    description = "Jaccard similarity between gene g's protein compartment flags and the union of compartment flags of p's target genes."
    rationale = "CRISPRa perturbations may affect genes whose proteins localize to the same compartments as the target, reflecting shared pathways."
    inputs = ["protein_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("protein_annotation")
        if not ann or "genes" not in ann or "columns" not in ann:
            return out

        cols = ann["columns"]
        col_idx = {c: i for i, c in enumerate(cols)}
        comp_cols = [col_idx[c] for c in _COMPARTMENTS if c in col_idx]
        if not comp_cols:
            return out

        genes_tbl = ann["genes"]
        n_genes = ctx.n_genes

        # Build a (n_genes, n_compartments) 0/1 matrix aligned to ctx.genes.
        comp_mat = np.zeros((n_genes, len(comp_cols)), dtype=float)
        for gi, g in enumerate(ctx.genes):
            vals = genes_tbl.get(g)
            if vals is None:
                continue
            for k, ci in enumerate(comp_cols):
                v = vals[ci]
                if v is not None and v == v:  # not NaN
                    try:
                        comp_mat[gi, k] = 1.0 if float(v) != 0.0 else 0.0
                    except (TypeError, ValueError):
                        comp_mat[gi, k] = 0.0

        # Cache union compartment vectors per perturbation id.
        cache = ctx.cache
        union_cache = cache.get("_tc_union_cache")
        if union_cache is None:
            union_cache = {}
            cache["_tc_union_cache"] = union_cache

        for i, p in enumerate(perts):
            uni = union_cache.get(p)
            if uni is None:
                tgt_idx = ctx.target_indices(p)
                if tgt_idx:
                    tgt_mat = comp_mat[np.asarray(tgt_idx, dtype=int), :]
                    uni = (tgt_mat.sum(axis=0) > 0).astype(float)
                else:
                    uni = np.zeros(len(comp_cols), dtype=float)
                union_cache[p] = uni

            union_size = uni.sum()
            if union_size == 0.0:
                # g's set union target set is empty only if g has no flags too
                continue

            inter = comp_mat * uni[None, :]  # (n_genes, n_comp)
            inter_size = inter.sum(axis=1)
            g_size = comp_mat.sum(axis=1)
            # |A U B| = |A| + |B| - |A n B|
            union_sizes = g_size + union_size - inter_size
            with np.errstate(divide="ignore", invalid="ignore"):
                jac = np.where(union_sizes > 0, inter_size / union_sizes, 0.0)
            out[i, :, 0] = jac

        out[~np.isfinite(out)] = 0.0
        return out
