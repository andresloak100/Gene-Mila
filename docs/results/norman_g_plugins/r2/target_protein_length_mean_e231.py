import numpy as np
from genemila.features.api import Feature, register


@register
class TargetProteinLengthMeanE231(Feature):
    name = "target_protein_length_mean_e231"
    version = 1
    description = "Mean protein length (UniProt) of the perturbation's target genes, same value for all genes."
    rationale = "Longer proteins may have more domains/interactions, leading to broader perturbation effects."
    inputs = ["protein_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))
        annot = ctx.knowledge("protein_annotation")
        if annot is None:
            return out
        cols = annot.get("columns", [])
        genes_tbl = annot.get("genes", {})
        try:
            pl_idx = cols.index("protein_length")
        except ValueError:
            return out

        cache = ctx.cache
        if "protein_length_map" not in cache:
            pl_map = {}
            for sym, vals in genes_tbl.items():
                if vals is None:
                    continue
                v = vals[pl_idx]
                if v is None:
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv):
                    pl_map[sym] = fv
            cache["protein_length_map"] = pl_map
        pl_map = cache["protein_length_map"]

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            vals = [pl_map[g] for g in tg if g in pl_map]
            if vals:
                out[i, :, 0] = float(np.mean(vals))
        return out
