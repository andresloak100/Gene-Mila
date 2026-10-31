import numpy as np
from genemila.features.api import Feature, register


@register
class NUpstreamAtgCountE58(Feature):
    name = "n_upstream_atg_count_e58"
    version = 1
    description = "Number of upstream ATG codons (n_upstream_atg) in the 5' UTR for gene g."
    rationale = ("Upstream ATGs can reduce translation efficiency and may correlate with "
                 "lower transcriptional response, potentially buffering perturbation effects.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        values = np.full(n_genes, np.nan, dtype=np.float64)

        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes_tbl = ann.get("genes", {}) if isinstance(ann, dict) else {}
            columns = ann.get("columns", []) if isinstance(ann, dict) else []
            try:
                col_idx = columns.index("n_upstream_atg")
            except (ValueError, AttributeError):
                col_idx = None

            if col_idx is not None:
                for g in ctx.genes:
                    row = genes_tbl.get(g)
                    if row is None:
                        continue
                    try:
                        val = row[col_idx]
                    except (IndexError, TypeError):
                        continue
                    if val is None:
                        continue
                    try:
                        fval = float(val)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fval):
                        gi = ctx.gene_index[g]
                        values[gi] = fval

        # Impute missing with column mean of observed values (finite only).
        finite_mask = np.isfinite(values)
        if finite_mask.any():
            fill = float(values[finite_mask].mean())
        else:
            fill = 0.0
        values[~finite_mask] = fill

        out = np.empty((len(perts), n_genes, 1), dtype=np.float64)
        out[:, :, 0] = values[np.newaxis, :]
        return out
