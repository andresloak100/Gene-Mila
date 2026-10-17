import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoeufXIsTarget(Feature):
    name = "target_loeuf_x_is_target_e240"
    version = 1
    description = "Product of target gene's LOEUF (oe_lof_upper) and is_target indicator."
    rationale = (
        "LoF-intolerant genes may show stronger/wider expression changes when perturbed, "
        "so the target's LOEUF modulates the target-specific effect."
    )
    inputs = ["control_cells", "knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        loeuf = np.full(n_genes, np.nan, dtype=float)

        constraint = None
        try:
            constraint = ctx.knowledge("gene_constraint")
        except Exception:
            constraint = None

        if constraint is not None:
            genes_map = constraint.get("genes", {}) or {}
            columns = constraint.get("columns", []) or []
            try:
                idx = list(columns).index("oe_lof_upper")
            except ValueError:
                idx = None
            if idx is not None:
                for gname, gi in ctx.gene_index.items():
                    vals = genes_map.get(gname)
                    if vals is None:
                        continue
                    try:
                        v = vals[idx]
                    except Exception:
                        continue
                    if v is None:
                        continue
                    try:
                        v = float(v)
                    except Exception:
                        continue
                    if np.isfinite(v):
                        loeuf[gi] = v

        # Fallback: if no LOEUF available at all, leave zeros (safe, finite).
        for i, p in enumerate(perts):
            tgt = ctx.target_indices(p)
            if not tgt:
                continue
            for gi in tgt:
                v = loeuf[gi]
                if np.isfinite(v):
                    out[i, gi, 0] = v

        out[~np.isfinite(out)] = 0.0
        return out
