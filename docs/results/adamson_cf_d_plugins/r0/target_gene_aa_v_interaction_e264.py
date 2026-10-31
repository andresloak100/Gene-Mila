import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGeneAaVInteractionE264(Feature):
    name = "target_gene_aa_v_interaction_e264"
    version = 1
    description = "Product of target gene's valine fraction (aa_V) and gene g's valine fraction."
    rationale = ("Valine-rich proteins may share hydrophobic interaction interfaces, "
                 "causing coordinated responses.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        aa_v = np.full(ctx.n_genes, np.nan, dtype=float)
        if ann is not None:
            cols = list(ann.get("columns", []))
            genes_map = ann.get("genes", {})
            if "aa_V" in cols:
                idx = cols.index("aa_V")
                for g, vals in genes_map.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None or vals is None:
                        continue
                    try:
                        v = vals[idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        aa_v[gi] = fv

        # Fill missing gene values with the mean of the observed ones (finite, no NaN).
        observed = np.isfinite(aa_v)
        if observed.any():
            fill = float(aa_v[observed].mean())
        else:
            fill = 0.0
        aa_v = np.where(observed, aa_v, fill)

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            tgt_v = float(np.mean(aa_v[tgt_idx]))
            out[i, :, 0] = tgt_v * aa_v

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
