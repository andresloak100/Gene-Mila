import numpy as np
from genemila.features.api import Feature, register


@register
class GeneCorrWithResidualGenes(Feature):
    name = "gene_corr_with_residual_genes_e141"
    version = 1
    description = ("Mean Pearson correlation of each gene's control expression with a fixed "
                   "set of residual-driving genes (HBZ, HBG2, HIST1H1C, ...), broadcast "
                   "across all perturbations.")
    rationale = ("Genes co-expressed with the residual-driving genes share the same "
                 "unexplained regulatory program and may have larger prediction errors.")
    inputs = ["control_cells"]
    params = {"residual_gene_list": ["HBZ", "HBG2", "HIST1H1C", "HBA1", "HBG1",
                                     "MS4A4A", "HIST1H2BK", "MT-ATP6"]}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        residual_genes = params.get("residual_gene_list", self.params["residual_gene_list"])

        X = np.asarray(ctx.control_cells, dtype=float)
        # Center and standardise columns (guard against zero variance)
        Xc = X - X.mean(axis=0, keepdims=True)
        norms = np.sqrt((Xc * Xc).sum(axis=0))
        norms_safe = np.where(norms > 0, norms, 1.0)
        Z = Xc / norms_safe

        # Indices of residual genes present in ctx
        resid_idx = [ctx.gene_index[g] for g in residual_genes if g in ctx.gene_index]

        if len(resid_idx) == 0:
            mean_corr = np.zeros(n_genes, dtype=float)
        else:
            # Correlation of every gene with each residual gene: (n_genes, n_resid)
            corr = Z.T @ Z[:, resid_idx]
            # Zero out correlations for genes with no variance
            valid = (norms > 0)
            corr[~valid, :] = 0.0
            mean_corr = corr.mean(axis=1)

        mean_corr = np.nan_to_num(mean_corr, nan=0.0, posinf=0.0, neginf=0.0)

        out = np.empty((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = mean_corr[None, :]
        return out
