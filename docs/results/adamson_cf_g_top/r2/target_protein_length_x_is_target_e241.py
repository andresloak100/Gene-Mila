import numpy as np
from genemila.features.api import Feature, register


@register
class TargetProteinLengthXIsTarget(Feature):
    name = "target_protein_length_x_is_target_e241"
    version = 1
    description = "Product of target gene's protein length and is_target indicator."
    rationale = (
        "Protein length of the target gene may modulate the magnitude/specificity "
        "of the perturbation response; an interaction term with the is_target "
        "indicator lets the model scale the target-gene effect by its protein length."
    )
    inputs = ["protein_annotation", "target_indices"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # Load protein annotation once and build a protein-length vector aligned
        # to ctx.genes. Missing / unmatched genes -> NaN, later treated as 0.
        cache = ctx.cache
        key = "__prot_len_vec_e241"
        if key not in cache:
            prot_len = np.full(n_genes, np.nan, dtype=float)
            ann = ctx.knowledge("protein_annotation")
            if ann is not None:
                cols = ann.get("columns", []) or []
                # find index of protein_length column
                pl_idx = None
                for j, c in enumerate(cols):
                    if str(c).strip().lower() == "protein_length":
                        pl_idx = j
                        break
                genes_map = ann.get("genes", {}) or {}
                if pl_idx is not None and isinstance(genes_map, dict):
                    for g, vals in genes_map.items():
                        gi = ctx.gene_index.get(g)
                        if gi is None:
                            continue
                        try:
                            v = vals[pl_idx]
                        except (IndexError, TypeError):
                            continue
                        if v is None:
                            continue
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv):
                            prot_len[gi] = fv
            # replace NaN with 0 for finite output
            prot_len = np.where(np.isfinite(prot_len), prot_len, 0.0)
            cache[key] = prot_len
        prot_len = cache[key]

        for i, p in enumerate(perts):
            tgt = ctx.target_indices(p)
            if not tgt:
                continue
            # protein length of the target gene(s); use the first target's length
            # (single-gene targets in this dataset). If multiple, take max length.
            lengths = prot_len[np.asarray(tgt, dtype=int)]
            val = float(np.max(lengths)) if lengths.size else 0.0
            if not np.isfinite(val):
                val = 0.0
            out[i, tgt, 0] = val

        return out
