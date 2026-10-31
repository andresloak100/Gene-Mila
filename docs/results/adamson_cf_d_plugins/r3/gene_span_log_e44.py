import numpy as np
from genemila.features.api import Feature, register


@register
class GeneSpanLogE44(Feature):
    name = "gene_span_log_e44"
    version = 1
    description = "Log10 of gene_span_kb for gene g."
    rationale = (
        "Longer genes have more opportunities for transcriptional pausing or "
        "chromatin-level regulation, dampening response magnitude."
    )
    inputs = ["knowledge:gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        vals = np.full(n, np.nan, dtype=float)

        if isinstance(ann, dict):
            genes = ann.get("genes") or {}
            columns = ann.get("columns") or []
            try:
                col_idx = list(columns).index("gene_span_kb")
            except ValueError:
                col_idx = 0
            for j, g in enumerate(ctx.genes):
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
                    vals[j] = fv

        # log10; non-positive or missing -> handled via median of valid logs
        valid = np.isfinite(vals) & (vals > 0)
        logs = np.full(n, np.nan, dtype=float)
        logs[valid] = np.log10(vals[valid])

        finite_logs = logs[np.isfinite(logs)]
        if finite_logs.size > 0:
            fill = float(np.median(finite_logs))
        else:
            fill = 0.0
        logs[~np.isfinite(logs)] = fill

        out[:, :, 0] = logs[None, :]
        return out
