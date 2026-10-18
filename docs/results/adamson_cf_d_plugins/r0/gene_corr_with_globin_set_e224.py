import numpy as np
from genemila.features.api import Feature, register

@register
class GeneCorrWithGlobinSetE224(Feature):
    name = "gene_corr_with_globin_set_e224"
    version = 1
    description = ("Maximum absolute Pearson correlation between gene g's expression "
                   "and each of HBZ, HBG2, HBA1, HBG1 across control cells.")
    rationale = ("Co-expression with globin genes reflects shared regulation by erythroid "
                 "transcription factors, whose perturbation response is a major residual component.")
    inputs = ["control_cells", "gene_corr"]
    params = {"globin_genes": ["HBZ", "HBG2", "HBA1", "HBG1"]}
    dim = 1

    def compute(self, ctx, perts, params):
        globin_genes = params.get("globin_genes", ["HBZ", "HBG2", "HBA1", "HBG1"])
        n_genes = ctx.n_genes

        # Resolve globin gene column indices
        globin_idx = [ctx.gene_index[g] for g in globin_genes if g in ctx.gene_index]

        # Compute max |corr| with globin set per gene
        if len(globin_idx) == 0:
            corr_summary = np.zeros(n_genes, dtype=float)
        else:
            # Use cached gene_corr matrix (n_genes x n_genes) if available via ctx.gene_corr
            # ctx.gene_corr is Pearson correlation across control cells
            gc = ctx.gene_corr  # (n_genes, n_genes)
            sub = gc[:, globin_idx]  # (n_genes, n_globin)
            corr_summary = np.max(np.abs(sub), axis=1)
            corr_summary = np.nan_to_num(corr_summary, nan=0.0, posinf=0.0, neginf=0.0)

        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = corr_summary[np.newaxis, :]
        return out
