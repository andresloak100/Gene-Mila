import numpy as np
from genemila.features.api import Feature, register

@register
class TargetProteinLengthE71(Feature):
    name = "target_protein_length_e71"
    version = 1
    description = "Protein length of the perturbation target gene (UniProt), as an interaction feature."
    rationale = "Longer proteins may have more regulatory sites or be more sensitive to perturbation, affecting downstream expression."
    inputs = ["protein_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("protein_annotation")
        if not ann:
            return out

        cols = ann.get("columns", [])
        genes_tab = ann.get("genes", {}) or {}
        try:
            pl_idx = cols.index("protein_length")
        except ValueError:
            return out

        # Build gene -> protein length map (finite, positive only)
        pl_map = {}
        for g, vals in genes_tab.items():
            if not vals:
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
            if np.isfinite(fv) and fv > 0:
                pl_map[g] = fv

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue
            vals = [pl_map[g] for g in targets if g in pl_map]
            if vals:
                out[i, :, 0] = float(np.mean(vals))
        return out
