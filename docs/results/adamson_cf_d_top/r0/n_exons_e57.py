import numpy as np
from genemila.features.api import Feature, register

@register
class NExonsE57(Feature):
    name = "n_exons_e57"
    version = 1
    description = "Number of exons for gene g from gene_annotation."
    rationale = ("Exon count reflects splicing complexity, which may modulate the "
                 "magnitude of expression changes after perturbations affecting "
                 "splicing or transcription.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        col = np.zeros(n_genes, dtype=float)
        if ann is not None:
            columns = ann.get("columns", [])
            genes_tbl = ann.get("genes", {}) or {}
            try:
                idx = columns.index("n_exons")
            except ValueError:
                idx = -1
            if idx >= 0:
                for gi, g in enumerate(ctx.genes):
                    vals = genes_tbl.get(g)
                    if vals is None:
                        continue
                    try:
                        v = vals[idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        col[gi] = fv

        # Same per-gene value for every perturbation row.
        out[:, :, 0] = col[None, :]
        return out
