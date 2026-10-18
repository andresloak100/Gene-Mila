import numpy as np
from genemila.features.api import Feature, register

@register
class CdsLengthE68(Feature):
    name = "cds_length_e68"
    version = 1
    description = "Coding sequence length (bp) of gene g from gene_annotation."
    rationale = "Longer CDS may have more stable transcripts or slower degradation, reducing observed delta."
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        ann = ctx.knowledge("gene_annotation")
        n_genes = ctx.n_genes
        vals = np.zeros(n_genes, dtype=float)
        if ann is not None:
            genes = ann.get("genes") or {}
            cols = ann.get("columns") or []
            try:
                ci = cols.index("cds_length")
            except ValueError:
                ci = None
            if ci is not None:
                for j, g in enumerate(ctx.genes):
                    row = genes.get(g)
                    if row is None:
                        continue
                    try:
                        v = row[ci]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        vals[j] = fv
        out = np.broadcast_to(vals[None, :, None], (len(perts), n_genes, 1)).copy()
        out[~np.isfinite(out)] = 0.0
        return out
