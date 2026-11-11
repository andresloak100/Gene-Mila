import numpy as np
from genemila.features.api import Feature, register

@register
class GlobinCoexpressionGeneE148(Feature):
    name = "globin_coexpression_gene_e148"
    version = 1
    description = "Mean absolute Pearson correlation of each gene's control expression with globin genes (HBZ, HBG2, HBA1, HBG1)."
    rationale = "Genes co-expressed with globins belong to the erythroid program and may respond to perturbations of related processes."
    inputs = ["control_cells"]
    params = {}
    dim = 1

    GLOBIN_GENES = ["HBZ", "HBG2", "HBA1", "HBG1"]

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        globin_idx = [ctx.gene_index[g] for g in self.GLOBIN_GENES if g in ctx.gene_index]

        if len(globin_idx) == 0:
            feat = np.zeros(n_genes, dtype=float)
        else:
            corr = np.asarray(ctx.gene_corr, dtype=float)
            sub = corr[:, globin_idx]
            sub = np.nan_to_num(sub, nan=0.0, posinf=0.0, neginf=0.0)
            feat = np.abs(sub).mean(axis=1)

        feat = np.nan_to_num(feat, nan=0.0, posinf=0.0, neginf=0.0)
        out = np.repeat(feat[None, :, None], len(perts), axis=0)
        return out.astype(float)
