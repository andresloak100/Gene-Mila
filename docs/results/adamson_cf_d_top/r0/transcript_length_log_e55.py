import numpy as np
from genemila.features.api import Feature, register


@register
class TranscriptLengthLogE55(Feature):
    name = "transcript_length_log_e55"
    version = 1
    description = "Log1p of the annotated transcript_length of gene g from gene_annotation."
    rationale = (
        "Longer transcripts may have different elongation/degradation dynamics and "
        "transcriptional pausing, altering the magnitude of expression changes after "
        "perturbation; length is expected to be negatively associated with response."
    )
    inputs = ["gene_annotation"]
    params = {"transform": "log1p"}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        vals = np.full(n_genes, np.nan, dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            columns = ann.get("columns", [])
            genes = ann.get("genes", {})
            try:
                col_idx = columns.index("transcript_length")
            except ValueError:
                col_idx = None
            if col_idx is not None:
                for i, g in enumerate(ctx.genes):
                    row = genes.get(g)
                    if row is None:
                        continue
                    try:
                        v = row[col_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        vals[i] = fv

        # Fallback for missing entries: use median of observed, else 0.
        finite = np.isfinite(vals)
        if finite.any():
            fill = float(np.median(vals[finite]))
        else:
            fill = 0.0
        vals[~finite] = fill

        # Apply transform (default log1p).
        transform = params.get("transform", "log1p") if params else "log1p"
        if transform == "log1p":
            vals = np.log1p(np.clip(vals, a_min=0.0, a_max=None))
        elif transform == "log":
            vals = np.log(np.clip(vals, a_min=1e-12, a_max=None))
        # "none" -> raw values

        vals = np.where(np.isfinite(vals), vals, 0.0)

        out = np.empty((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = vals[np.newaxis, :]
        return out
