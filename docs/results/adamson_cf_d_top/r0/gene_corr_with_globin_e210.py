import numpy as np
from genemila.features.api import Feature, register

@register
class GeneCorrWithGlobin(Feature):
    name = "gene_corr_with_globin_e210"
    version = 1
    description = "Average Pearson correlation of each gene's control-cell expression with globin genes (HBZ, HBG2, HBA1)."
    rationale = "Co-expression with globin genes marks genes in the erythroid/globin regulatory program that respond to certain perturbations."
    inputs = ["control_cells", "gene_corr"]
    params = {"globin_genes": ["HBZ", "HBG2", "HBA1"]}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        globin_genes = params.get("globin_genes", ["HBZ", "HBG2", "HBA1"])

        # Resolve globin gene columns
        idx = [ctx.gene_index[g] for g in globin_genes if g in ctx.gene_index]
        if not idx:
            return np.zeros((len(perts), n_genes, 1))

        # Use cached gene correlation matrix if available
        corr = ctx.gene_corr  # (n_genes, n_genes)
        if corr is not None:
            vals = corr[:, idx].mean(axis=1)
        else:
            # Fallback: compute from control cells directly
            X = ctx.control_cells
            Xc = X - X.mean(axis=0, keepdims=True)
            std = Xc.std(axis=0)
            std[std == 0] = 1.0
            Xn = Xc / std
            G = Xn[:, idx].mean(axis=1)  # mean globin vector
            Gc = G - G.mean()
            Gnorm = np.linalg.norm(Gc)
            if Gnorm == 0:
                vals = np.zeros(n_genes)
            else:
                vals = (Xn * Gc[:, None]).sum(axis=0) / (np.linalg.norm(Xn, axis=0) * Gnorm + 1e-12)

        vals = np.nan_to_num(vals, nan=0.0, posinf=0.0, neginf=0.0)
        out = np.broadcast_to(vals[None, :, None], (len(perts), n_genes, 1)).copy()
        return out
