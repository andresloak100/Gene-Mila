import numpy as np
from genemila.features.api import Feature, register

@register
class Utr5LengthE94E99(Feature):
    name = "utr5_length_e94_e99"
    version = 1
    description = "Length of the 5' UTR of gene g from gene_annotation."
    rationale = ("Longer 5' UTRs often contain regulatory elements that reduce translation "
                 "efficiency, buffering the protein-level impact of transcriptional perturbations.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        ka = ctx.knowledge("gene_annotation")
        n = ctx.n_genes
        vals = np.zeros(n, dtype=float)

        if ka is not None:
            columns = ka.get("columns", [])
            genes_tbl = ka.get("genes", {}) or {}
            try:
                col_idx = columns.index("utr5_length")
            except ValueError:
                col_idx = None

            if col_idx is not None:
                for g, colname in enumerate(ctx.genes):
                    row = genes_tbl.get(colname)
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
                        vals[g] = fv

        # Standardise for numerical stability across the model.
        mu = vals.mean()
        sd = vals.std()
        if sd > 0 and np.isfinite(sd):
            vals = (vals - mu) / sd
        else:
            vals = np.zeros_like(vals)

        out = np.empty((len(perts), n, 1), dtype=float)
        out[:, :, 0] = vals[None, :]
        out[~np.isfinite(out)] = 0.0
        return out
