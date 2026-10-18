import numpy as np
from genemila.features.api import Feature, register

@register
class TargetErFlagE11(Feature):
    name = "target_er_flag_e11"
    version = 1
    description = "Indicator that the targeted gene's protein is annotated as endoplasmic_reticulum or membrane."
    rationale = "Perturbing ER/membrane proteins triggers ER stress or secretory pathway responses, altering gene expression programs."
    inputs = ["protein_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))
        ann = ctx.knowledge("protein_annotation")
        if ann is None:
            return out
        cols = ann.get("columns", [])
        genes = ann.get("genes", {})
        try:
            i_er = cols.index("endoplasmic_reticulum")
        except ValueError:
            i_er = None
        try:
            i_mem = cols.index("membrane")
        except ValueError:
            i_mem = None
        if i_er is None and i_mem is None:
            return out
        for i, p in enumerate(perts):
            flag = 0.0
            for g in ctx.target_genes(p):
                vals = genes.get(g)
                if vals is None:
                    continue
                if i_er is not None and i_er < len(vals) and vals[i_er]:
                    flag = 1.0
                    break
                if i_mem is not None and i_mem < len(vals) and vals[i_mem]:
                    flag = 1.0
                    break
            out[i, :, 0] = flag
        return out
