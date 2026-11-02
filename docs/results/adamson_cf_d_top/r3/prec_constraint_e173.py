import numpy as np
from genemila.features.api import Feature, register


@register
class PrecConstraintE173(Feature):
    name = "prec_constraint_e173"
    version = 1
    description = "Per-gene pRec value from gene_constraint, with missing values imputed to the median."
    rationale = ("Genes intolerant to recessive loss-of-function may have smaller expression "
                 "changes due to tighter regulation.")
    inputs = ["gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        genes = ctx.genes

        vals = np.full(n_genes, np.nan, dtype=float)

        table = ctx.knowledge("gene_constraint")
        if table is not None:
            columns = table.get("columns", [])
            gene_data = table.get("genes", {}) or {}

            # Locate the pRec column (case-insensitive match).
            prec_idx = None
            for j, c in enumerate(columns):
                if str(c).strip().lower() == "prec":
                    prec_idx = j
                    break

            if prec_idx is not None:
                for g in genes:
                    row = gene_data.get(g)
                    if row is None:
                        continue
                    try:
                        v = row[prec_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        vals[ctx.gene_index[g]] = fv

        # Impute missing values with the median of the observed values.
        observed = np.isfinite(vals)
        if observed.any():
            median = float(np.median(vals[observed]))
        else:
            median = 0.0
        vals[~observed] = median

        # Feature is identical for every perturbation: broadcast across rows.
        out = np.empty((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = vals[None, :]
        return out
