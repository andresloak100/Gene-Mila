import numpy as np
from genemila.features.api import Feature, register

@register
class GeneCorrWithResidualSet(Feature):
    name = "gene_corr_with_residual_set_e182_e184"
    version = 1
    description = ("Mean absolute control-expression correlation of each gene with a "
                   "residual-set of globin/histone/other genes (HBZ, HBG2, HIST1H1C, "
                   "HBA1, HBG1, MS4A4A, HIST1H2BK, MT-ATP6).")
    rationale = ("The residual component is enriched for globin and histone genes; genes "
                 "co-expressed with them may share regulatory programs and thus respond "
                 "similarly to perturbation.")
    inputs = ["gene_corr"]
    params = {}
    dim = 1

    RESIDUAL_GENES = ["HBZ", "HBG2", "HIST1H1C", "HBA1", "HBG1",
                      "MS4A4A", "HIST1H2BK", "MT-ATP6"]

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        corr = ctx.gene_corr

        idx = [ctx.gene_index[g] for g in self.RESIDUAL_GENES if g in ctx.gene_index]
        if len(idx) == 0:
            vec = np.zeros(n_genes, dtype=float)
        else:
            sub = corr[:, idx]  # (n_genes, n_residual)
            sub = np.abs(np.nan_to_num(sub, nan=0.0))
            vec = sub.mean(axis=1)

        vec = np.nan_to_num(vec, nan=0.0, posinf=0.0, neginf=0.0)
        out = np.broadcast_to(vec[None, :, None], (len(perts), n_genes, 1)).copy()
        return out
