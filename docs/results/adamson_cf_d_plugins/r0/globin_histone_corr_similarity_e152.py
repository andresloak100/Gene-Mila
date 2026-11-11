import numpy as np
from genemila.features.api import Feature, register

@register
class GlobinHistoneCorrSimilarity(Feature):
    name = "globin_histone_corr_similarity_e152"
    version = 1
    description = ("Max absolute Pearson correlation of each gene's control expression with "
                   "residual-driving globin/histone genes (HBZ, HBG2, HBA1, HBG1, HIST1H1C, HIST1H2BK).")
    rationale = ("Genes co-expressed with globin/histone genes may share regulatory programs "
                 "that respond similarly to perturbations.")
    inputs = ["gene_corr"]
    params = {}
    dim = 1

    _DRIVERS = ["HBZ", "HBG2", "HBA1", "HBG1", "HIST1H1C", "HIST1H2BK"]

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        # Resolve driver gene indices
        driver_idx = [ctx.gene_index[g] for g in self._DRIVERS if g in ctx.gene_index]

        if len(driver_idx) == 0:
            vals = np.zeros(n_genes, dtype=float)
        else:
            corr = np.asarray(ctx.gene_corr, dtype=float)  # (n_genes, n_genes)
            sub = corr[:, driver_idx]  # (n_genes, n_drivers)
            sub = np.abs(sub)
            sub = np.where(np.isfinite(sub), sub, 0.0)
            vals = sub.max(axis=1)

        vals = np.nan_to_num(vals, nan=0.0, posinf=0.0, neginf=0.0)
        out = np.empty((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = vals[None, :]
        return out
