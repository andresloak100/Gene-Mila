import numpy as np
from genemila.features.api import Feature, register


@register
class ObsLofE114(Feature):
    name = "obs_lof_e114"
    version = 1
    description = "Observed number of loss-of-function variants for gene g from gene_constraint."
    rationale = (
        "Genes tolerant to loss-of-function mutations may have more regulatory redundancy "
        "and show smaller expression changes upon perturbation."
    )
    inputs = ["gene_constraint"]
    params = {"missing_value": 0}
    dim = 1

    def compute(self, ctx, perts, params):
        missing = float(params.get("missing_value", 0))
        n_genes = ctx.n_genes
        out = np.full((len(perts), n_genes, 1), missing, dtype=float)

        table = ctx.knowledge("gene_constraint")
        if table is None:
            return out

        genes_tbl = table.get("genes", {}) or {}
        columns = table.get("columns", []) or []
        try:
            col_idx = columns.index("obs_lof")
        except ValueError:
            return out

        vals = np.full(n_genes, missing, dtype=float)
        for gi, g in enumerate(ctx.genes):
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

        out[:, :, 0] = vals[None, :]
        return out
