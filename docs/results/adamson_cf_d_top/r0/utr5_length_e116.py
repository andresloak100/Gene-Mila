import numpy as np
from genemila.features.api import Feature, register


@register
class Utr5LengthE116(Feature):
    name = "utr5_length_e116"
    version = 1
    description = "Length of the 5' UTR for gene g from gene_annotation."
    rationale = ("Longer 5' UTRs may harbor regulatory motifs that stabilize expression "
                 "and reduce perturbation response.")
    inputs = ["gene_annotation"]
    params = {"missing_value": "median"}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        genes = ctx.genes

        ann = ctx.knowledge("gene_annotation")
        values = np.full(n_genes, np.nan, dtype=float)

        if ann is not None:
            ann_genes = ann.get("genes", {})
            columns = ann.get("columns", [])
            try:
                col_idx = columns.index("utr5_length")
            except ValueError:
                col_idx = None

            if col_idx is not None:
                for j, g in enumerate(genes):
                    rec = ann_genes.get(g)
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
                        values[j] = fv

        # Fill missing values
        missing = ~np.isfinite(values)
        if missing.any():
            if np.isfinite(values).any():
                fill = np.nanmedian(values)
            else:
                fill = 0.0
            mv = params.get("missing_value", "median")
            if isinstance(mv, (int, float)) and np.isfinite(mv):
                fill = float(mv)
            values[missing] = fill

        # Same value for every perturbation: shape (n_perts, n_genes, 1)
        out = np.repeat(values[:, None][None, :, :], len(perts), axis=0)
        return out
