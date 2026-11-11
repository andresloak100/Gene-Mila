import numpy as np
from genemila.features.api import Feature, register

@register
class AAHistidineFractionE144(Feature):
    name = "aa_histidine_fraction_e144"
    version = 1
    description = "Fraction of histidine residues in the protein of gene g from gene_annotation."
    rationale = ("Histidine-rich proteins are involved in metal binding and pH regulation, "
                 "linking them to stress responses.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is None:
            return out

        genes = ann.get("genes", {})
        columns = ann.get("columns", [])
        try:
            h_idx = columns.index("aa_H")
        except ValueError:
            return out

        vec = np.zeros(ctx.n_genes, dtype=float)
        for g, col in ctx.gene_index.items():
            vals = genes.get(g)
            if vals is None:
                continue
            v = vals[h_idx]
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv):
                vec[col] = fv

        out[:, :, 0] = vec[None, :]
        return out
