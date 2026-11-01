import numpy as np
from genemila.features.api import Feature, register


@register
class LofConstraintE8(Feature):
    name = "lof_constraint_e8"
    version = 1
    description = "Per-gene z-scored LOEUF (oe_lof_upper) from gnomAD LoF constraint; missing imputed with median."
    rationale = "LoF-intolerant genes are under stronger selective pressure to maintain expression, so their response to perturbation is damped (predicted negative coefficient)."
    inputs = ["gene_constraint"]
    params = {"impute": "median", "normalize": "zscore"}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        vals = np.full(n_genes, np.nan, dtype=float)

        kc = ctx.knowledge("gene_constraint")
        genes_table = {}
        if isinstance(kc, dict):
            genes_table = kc.get("genes", {}) or {}

        # Determine column index for oe_lof_upper
        cols = None
        if isinstance(kc, dict):
            cols = kc.get("columns")
        col_idx = None
        if isinstance(cols, (list, tuple)):
            for j, c in enumerate(cols):
                if isinstance(c, str) and c.strip().lower() == "oe_lof_upper":
                    col_idx = j
                    break

        for gi, g in enumerate(ctx.genes):
            entry = genes_table.get(g)
            if entry is None:
                continue
            v = None
            if col_idx is not None and isinstance(entry, (list, tuple)) and col_idx < len(entry):
                v = entry[col_idx]
            elif isinstance(entry, dict):
                v = entry.get("oe_lof_upper")
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv):
                vals[gi] = fv

        observed = vals[np.isfinite(vals)]
        if observed.size == 0:
            vec = np.zeros(n_genes, dtype=float)
        else:
            med = float(np.median(observed))
            filled = np.where(np.isfinite(vals), vals, med)
            mu = float(np.mean(filled))
            sd = float(np.std(filled))
            if sd > 0:
                vec = (filled - mu) / sd
            else:
                vec = np.zeros(n_genes, dtype=float)

        out = np.empty((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = vec[None, :]
        # ensure finite
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
