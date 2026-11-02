import numpy as np
from genemila.features.api import Feature, register


@register
class Utr3LengthGeneE113E128(Feature):
    name = "utr3_length_gene_e113_e128"
    version = 1
    description = "Length of the 3' untranslated region (UTR) of gene g in base pairs."
    rationale = (
        "Long 3' UTRs contain miRNA binding sites and other regulatory elements that "
        "can modulate mRNA stability, reducing the magnitude of expression changes."
    )
    inputs = ["gene_annotation"]
    params = {"log_transform": True, "impute": "median"}
    dim = 1

    def compute(self, ctx, perts, params):
        log_transform = params.get("log_transform", True)
        impute = params.get("impute", "median")

        ann = ctx.knowledge("gene_annotation")
        n_genes = ctx.n_genes

        # Build per-gene value vector aligned to ctx.genes order.
        vals = np.full(n_genes, np.nan, dtype=np.float64)

        if ann is not None:
            columns = ann.get("columns", [])
            try:
                col_idx = columns.index("utr3_length")
            except ValueError:
                col_idx = None
            genes_tbl = ann.get("genes", {}) or {}
            if col_idx is not None:
                for g, col in ctx.gene_index.items():
                    row = genes_tbl.get(g)
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
                        vals[col] = fv

        # Impute missing values.
        finite_mask = np.isfinite(vals)
        if impute == "median":
            if finite_mask.any():
                fill = float(np.median(vals[finite_mask]))
            else:
                fill = 0.0
        elif impute == "mean":
            if finite_mask.any():
                fill = float(np.mean(vals[finite_mask]))
            else:
                fill = 0.0
        else:  # "zero" or anything else
            fill = 0.0
        vals = np.where(finite_mask, vals, fill)

        # Log-transform (log1p) since lengths are non-negative; safe for all values.
        if log_transform:
            vals = np.log1p(np.clip(vals, 0.0, None))

        # Broadcast to (n_perts, n_genes, 1)
        out = np.repeat(vals[np.newaxis, :, np.newaxis], len(perts), axis=0)
        return out.astype(np.float64)
