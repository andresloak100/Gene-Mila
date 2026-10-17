import numpy as np
from genemila.features.api import Feature, register


@register
class ConstraintProductE594(Feature):
    name = "constraint_product_exxx_e594"
    version = 1
    description = "Product of (1 - LOEUF) of the perturbation target and (1 - LOEUF) of gene g."
    rationale = "Constraint reflects essentiality and network centrality; the joint product of target and gene constraint may predict stronger responses for functionally linked constrained genes."
    inputs = ["control_mean", "gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        constraint = ctx.knowledge("gene_constraint")

        # Build per-gene (1 - LOEUF) vector; default to 0.5 (neutral) where missing.
        loeuf = np.full(n_genes, np.nan, dtype=float)
        if constraint is not None and isinstance(constraint, dict):
            genes_map = constraint.get("genes", {})
            columns = constraint.get("columns", [])
            try:
                loeuf_idx = list(columns).index("oe_lof_upper")
            except (ValueError, TypeError):
                loeuf_idx = None
            if loeuf_idx is not None and isinstance(genes_map, dict):
                for g, vals in genes_map.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None:
                        continue
                    try:
                        v = vals[loeuf_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        loeuf[gi] = float(v)
                    except (ValueError, TypeError):
                        continue

        # Fill missing LOEUF with a neutral value (median of observed, else 0.5).
        observed = loeuf[np.isfinite(loeuf)]
        fill = float(np.median(observed)) if observed.size > 0 else 0.5
        loeuf = np.where(np.isfinite(loeuf), loeuf, fill)
        # Clamp to [0,1] defensively.
        loeuf = np.clip(loeuf, 0.0, 1.0)
        one_minus = 1.0 - loeuf  # (n_genes,)

        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if len(tgt_idx) == 0:
                # No measured target: default neutral target factor.
                tgt_factor = 0.5
            else:
                tgt_factor = float(np.mean(one_minus[tgt_idx]))
            out[i, :, 0] = tgt_factor * one_minus
        return out
