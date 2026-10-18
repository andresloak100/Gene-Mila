import numpy as np
from genemila.features.api import Feature, register


@register
class TargetResponseGCInteraction(Feature):
    name = "target_response_gc_interaction_e66_e78"
    version = 1
    description = (
        "Interaction between the gc_cds of the perturbation target gene and the "
        "gc_cds of each response gene (product or absolute difference)."
    )
    rationale = (
        "mRNA stability of target and response gene jointly determine the magnitude "
        "of perturbation response through transcript degradation machinery."
    )
    inputs = ["gene_annotation"]
    params = {"interaction_type": "product"}
    dim = 1

    def compute(self, ctx, perts, params):
        ann = ctx.knowledge("gene_annotation")
        interaction_type = params.get("interaction_type", "product")

        n_genes = ctx.n_genes
        # Build per-gene gc_cds vector aligned to ctx.genes, impute with median.
        gc_vals = np.full(n_genes, np.nan, dtype=float)
        if ann is not None:
            genes_table = ann.get("genes", {}) or {}
            columns = ann.get("columns", []) or []
            try:
                col_idx = columns.index("gc_cds")
            except ValueError:
                col_idx = None
            if col_idx is not None:
                for i, g in enumerate(ctx.genes):
                    entry = genes_table.get(g)
                    if entry is None:
                        continue
                    try:
                        v = entry[col_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        gc_vals[i] = fv

        finite_mask = np.isfinite(gc_vals)
        if finite_mask.any():
            median_val = float(np.median(gc_vals[finite_mask]))
        else:
            median_val = 0.0
        gc_vals[~finite_mask] = median_val

        # Cache target gc per perturbation id.
        cache = ctx.cache
        key = "_trgc_gc_vals"
        if key not in cache:
            cache[key] = gc_vals
        gc_vec = cache[key]

        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if tgt_idx:
                tgt_gc = float(np.mean([gc_vec[j] for j in tgt_idx]))
            else:
                tgt_gc = median_val

            if interaction_type == "difference":
                out[i, :, 0] = np.abs(tgt_gc - gc_vec)
            else:
                out[i, :, 0] = tgt_gc * gc_vec

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
