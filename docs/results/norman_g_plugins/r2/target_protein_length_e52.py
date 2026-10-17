import numpy as np
from genemila.features.api import Feature, register


@register
class TargetProteinLengthE52(Feature):
    name = "target_protein_length_e52"
    version = 1
    description = "Average protein length (UniProt) of perturbation p's target gene(s)."
    rationale = "Longer proteins may mediate more complex interactions, giving larger or more specific expression changes when activated."
    inputs = ["protein_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("protein_annotation")
        if ann is None:
            return out

        genes_tbl = ann.get("genes", {})
        columns = ann.get("columns", [])
        try:
            pl_idx = columns.index("protein_length")
        except ValueError:
            return out

        # Cache per-gene protein length lookups.
        cache = ctx.cache
        if "_e52_pl" not in cache:
            pl = {}
            for g, vals in genes_tbl.items():
                if vals is None or len(vals) <= pl_idx:
                    continue
                v = vals[pl_idx]
                if v is None:
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv):
                    pl[g] = fv
            cache["_e52_pl"] = pl
        pl = cache["_e52_pl"]

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue
            vals = [pl[g] for g in targets if g in pl]
            if not vals:
                continue
            out[i, :, 0] = float(np.mean(vals))

        return out
