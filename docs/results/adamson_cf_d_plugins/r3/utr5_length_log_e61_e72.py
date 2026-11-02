import numpy as np
from genemila.features.api import Feature, register

@register
class Utr5LengthLogE61E72(Feature):
    name = "utr5_length_log_e61_e72"
    version = 1
    description = "Log2 of 5' UTR length of gene g (per-gene, perturbation-independent)."
    rationale = ("Longer 5' UTRs often contain regulatory elements that modulate translation "
                 "initiation, affecting how gene expression responds to perturbations.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        vals = np.full(n_genes, np.nan, dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes_tbl = ann.get("genes", {}) or {}
            cols = ann.get("columns", []) or []
            try:
                col_idx = cols.index("utr5_length")
            except ValueError:
                col_idx = None
            if col_idx is not None:
                for g, gi in ctx.gene_index.items():
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
                        vals[gi] = fv

        finite = np.isfinite(vals)
        if finite.any():
            med = float(np.median(vals[finite]))
        else:
            med = 0.0
        vals = np.where(finite, vals, med)

        logged = np.log2(np.maximum(vals, 0.0) + 1.0)

        out = np.empty((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = logged[None, :]
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
