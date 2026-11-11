import numpy as np
from genemila.features.api import Feature, register


@register
class PLIDirectE91(Feature):
    name = "pli_direct_e91"
    version = 1
    description = "Continuous feature: pLI value for gene g from gene_constraint."
    rationale = ("Loss-of-function intolerant genes are under strong selection and have "
                 "buffered expression responses to perturbations.")
    inputs = ["gene_constraint"]
    params = {"column": "pLI", "impute": "median"}
    dim = 1

    def compute(self, ctx, perts, params):
        col = params.get("column", "pLI")
        impute = params.get("impute", "median")

        cache = ctx.cache
        key = ("pli_direct_e91", col, impute)
        if key not in cache:
            n_genes = ctx.n_genes
            vals = np.full(n_genes, np.nan, dtype=np.float64)

            kc = ctx.knowledge("gene_constraint")
            if kc is not None:
                columns = kc.get("columns", [])
                try:
                    col_idx = columns.index(col)
                except ValueError:
                    col_idx = None
                genes_tab = kc.get("genes", {}) or {}
                if col_idx is not None:
                    for gname, gvals in genes_tab.items():
                        gi = ctx.gene_index.get(gname)
                        if gi is None:
                            continue
                        if gvals is None:
                            continue
                        try:
                            v = gvals[col_idx]
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

            finite_mask = np.isfinite(vals)
            if impute == "median" and finite_mask.any():
                fill = float(np.median(vals[finite_mask]))
            elif impute == "mean" and finite_mask.any():
                fill = float(np.mean(vals[finite_mask]))
            else:
                fill = 0.0
            vals[~finite_mask] = fill

            cache[key] = vals

        gene_vals = cache[key]
        out = np.empty((len(perts), ctx.n_genes, 1), dtype=np.float64)
        out[:, :, 0] = gene_vals[np.newaxis, :]
        return out
