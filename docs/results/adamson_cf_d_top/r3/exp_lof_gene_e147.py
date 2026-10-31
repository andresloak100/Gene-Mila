import numpy as np
from genemila.features.api import Feature, register


@register
class ExpLofGeneE147(Feature):
    name = "exp_lof_gene_e147"
    version = 1
    description = "log1p of observed loss-of-function variant count per gene (gene_constraint.exp_lof), median-imputed."
    rationale = "Genes tolerant to LoF (more observed LoF variants) may show smaller expression changes upon perturbation."
    inputs = ["gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        vals = np.full(n_genes, np.nan, dtype=float)

        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            genes = kc.get("genes", {}) or {}
            columns = kc.get("columns", []) or []
            try:
                col_idx = list(columns).index("exp_lof")
            except ValueError:
                col_idx = None
            if col_idx is not None:
                for g in ctx.genes:
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
                        vals[ctx.gene_index[g]] = fv

        finite = np.isfinite(vals)
        if finite.any():
            med = float(np.median(vals[finite]))
        else:
            med = 0.0
        vals[~finite] = med

        transformed = np.log1p(np.maximum(vals, 0.0))
        out = np.empty((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = transformed[None, :]
        out[~np.isfinite(out)] = 0.0
        return out
