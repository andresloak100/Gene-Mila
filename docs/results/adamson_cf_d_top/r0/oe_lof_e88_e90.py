import numpy as np
from genemila.features.api import Feature, register


@register
class OeLofE88E90(Feature):
    name = "oe_lof_e88_e90"
    version = 1
    description = "Observed/expected loss-of-function ratio (oe_lof) for gene g from gene_constraint."
    rationale = (
        "Loss-of-function intolerant genes (low oe_lof) are more essential, so their "
        "perturbation causes larger expression changes in downstream genes; oe_lof "
        "quantifies tolerance to LoF."
    )
    inputs = ["gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        gc = ctx.knowledge("gene_constraint")
        if gc is None:
            return out

        genes_tbl = gc.get("genes", {})
        columns = gc.get("columns", [])

        # Locate the oe_lof column index.
        oe_idx = None
        for i, c in enumerate(columns):
            if c == "oe_lof":
                oe_idx = i
                break
        if oe_idx is None:
            # Fall back: some bundles use oe_lof_upper as LOEUF; prefer exact oe_lof.
            for i, c in enumerate(columns):
                if "oe_lof" in c and "upper" not in c:
                    oe_idx = i
                    break
        if oe_idx is None:
            return out

        # Build per-gene oe_lof vector aligned to ctx.genes.
        vec = np.full(ctx.n_genes, np.nan, dtype=float)
        for g, col_idx in ctx.gene_index.items():
            vals = genes_tbl.get(g)
            if vals is None:
                continue
            try:
                v = vals[oe_idx]
            except (IndexError, TypeError):
                continue
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv):
                vec[col_idx] = fv

        # Impute missing values with the mean of observed values (0 if none).
        finite_mask = np.isfinite(vec)
        if finite_mask.any():
            fill = float(vec[finite_mask].mean())
        else:
            fill = 0.0
        vec = np.where(finite_mask, vec, fill)

        # Broadcast to all perturbations.
        out[:, :, 0] = vec[None, :]
        return out
