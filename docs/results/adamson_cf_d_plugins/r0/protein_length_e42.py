import numpy as np
from genemila.features.api import Feature, register


@register
class ProteinLengthE42(Feature):
    name = "protein_length_e42"
    version = 1
    description = "Protein length in amino acids for gene g from protein_annotation."
    rationale = ("Longer proteins may be more stable or have slower turnover, "
                 "attenuating expression changes after perturbation.")
    inputs = ["protein_annotation.protein_length"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        n_genes = ctx.n_genes
        out = np.zeros((n_perts, n_genes, 1), dtype=float)

        pa = ctx.knowledge("protein_annotation")
        if not pa:
            return out

        cols = pa.get("columns", [])
        try:
            li = cols.index("protein_length")
        except ValueError:
            return out

        genes_tbl = pa.get("genes", {}) or {}
        vec = np.zeros(n_genes, dtype=float)
        for j, g in enumerate(ctx.genes):
            vals = genes_tbl.get(g)
            if not vals:
                continue
            v = vals[li]
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv):
                vec[j] = fv

        out[:, :, 0] = vec[np.newaxis, :]
        return out
