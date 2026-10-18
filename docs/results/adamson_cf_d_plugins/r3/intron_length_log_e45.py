import numpy as np
from genemila.features.api import Feature, register

@register
class IntronLengthLogE45(Feature):
    name = "intron_length_log_e45"
    version = 1
    description = "Log10 of gene_annotation.intron_length_kb for gene g, missing -> median."
    rationale = ("Long introns slow transcription and mRNA maturation, reducing the observed "
                 "expression change within the measurement window; predicted negative coefficient.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        vals = np.full(n, np.nan, dtype=float)

        ka = ctx.knowledge("gene_annotation")
        if ka is not None:
            cols = ka.get("columns", [])
            genes = ka.get("genes", {}) or {}
            try:
                ci = cols.index("intron_length_kb")
            except (ValueError, AttributeError):
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
                        v = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(v) and v > 0:
                        vals[j] = np.log10(v)

        finite = np.isfinite(vals)
        if finite.any():
            med = float(np.median(vals[finite]))
        else:
            med = 0.0
        vals[~finite] = med

        out = np.broadcast_to(vals[None, :, None], (len(perts), n, 1)).copy()
        return out
