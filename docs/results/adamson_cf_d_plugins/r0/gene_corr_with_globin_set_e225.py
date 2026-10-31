import numpy as np
from genemila.features.api import Feature, register


@register
class GeneCorrWithGlobinSetE225(Feature):
    name = "gene_corr_with_globin_set_e225"
    version = 1
    description = ("Maximum absolute Pearson correlation between gene g's expression "
                   "and each of a set of globin genes across control cells.")
    rationale = ("Co-expression with globin genes reflects shared regulation by erythroid "
                 "transcription factors, whose perturbation response is a major residual component.")
    inputs = ["gene_corr"]
    params = {"globin_genes": ["HBZ", "HBG2", "HBA1", "HBG1"]}
    dim = 1

    def compute(self, ctx, perts, params):
        globin_genes = params.get("globin_genes", ["HBZ", "HBG2", "HBA1", "HBG1"])
        n_genes = ctx.n_genes

        # Resolve globin gene columns
        gidx = [ctx.gene_index[g] for g in globin_genes if g in ctx.gene_index]

        if len(gidx) == 0:
            summary = np.zeros(n_genes, dtype=float)
        else:
            gene_corr = ctx.gene_corr
            # (n_genes, n_globin) submatrix of correlations
            sub = gene_corr[:, gidx]
            # max absolute correlation per gene
            summary = np.max(np.abs(sub), axis=1)
            summary = np.nan_to_num(summary, nan=0.0, posinf=0.0, neginf=0.0)

        # Same vector for every perturbation row
        out = np.repeat(summary[None, :, None], len(perts), axis=0)
        return out
