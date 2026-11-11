import numpy as np
from genemila.features.api import Feature, register


@register
class NTranscriptsLogE49(Feature):
    name = "n_transcripts_log_e49"
    version = 1
    description = "Log10 of n_transcripts for gene g (missing -> median)."
    rationale = ("Multiple isoforms provide redundancy and regulatory flexibility, "
                 "reducing net expression change after perturbation.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        values = np.full(n_genes, np.nan, dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes = ann.get("genes", {}) or {}
            columns = ann.get("columns", []) or []
            try:
                col_idx = columns.index("n_transcripts")
            except (ValueError, AttributeError):
                col_idx = None

            if col_idx is not None:
                for gi, g in enumerate(ctx.genes):
                    rec = genes.get(g)
                    if rec is None:
                        continue
                    try:
                        v = rec[col_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        values[gi] = fv

        finite = np.isfinite(values)
        if finite.any():
            median = float(np.median(values[finite]))
        else:
            median = 1.0
        values[~finite] = median

        # log10, guarding against non-positive values
        positive = values > 0
        log_vals = np.zeros_like(values)
        log_vals[positive] = np.log10(values[positive])
        # for non-positive, fall back to log10(median) or 0
        if median > 0:
            log_vals[~positive] = np.log10(median)
        else:
            log_vals[~positive] = 0.0

        out = np.broadcast_to(log_vals[None, :, None],
                              (len(perts), n_genes, 1)).copy()
        return out
