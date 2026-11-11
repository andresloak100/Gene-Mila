import numpy as np
from genemila.features.api import Feature, register


@register
class GeneCorrWithGlobin(Feature):
    name = "gene_corr_with_globin_e194_e195"
    version = 1
    description = "Max |Pearson correlation| of gene g with any globin gene (HBZ, HBG2, HBA1, HBG1) across control cells."
    rationale = ("High co-expression with globin genes marks genes in the same erythroid/globin "
                 "regulatory program, which is already perturbed and thus shows smaller additional changes.")
    inputs = ["gene_corr"]
    params = {"globin_genes": ["HBZ", "HBG2", "HBA1", "HBG1"]}
    dim = 1

    def compute(self, ctx, perts, params):
        globin_genes = params.get("globin_genes", ["HBZ", "HBG2", "HBA1", "HBG1"])
        corr = ctx.gene_corr
        idx = [ctx.gene_index[g] for g in globin_genes if g in ctx.gene_index]
        if len(idx) == 0:
            feat = np.zeros(ctx.n_genes, dtype=float)
        else:
            feat = np.abs(corr[:, idx]).max(axis=1)
        feat = np.nan_to_num(feat, nan=0.0, posinf=0.0, neginf=0.0)
        out = np.repeat(feat[:, None], len(perts), axis=1).T
        return out[:, :, None]
