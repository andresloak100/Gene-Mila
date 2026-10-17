import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoEUFxIsTarget(Feature):
    name = "target_loeuf_x_is_target_e286"
    version = 1
    description = "Product of target gene's LOEUF (oe_lof_upper) and is_target indicator."
    rationale = (
        "LoF-intolerant (low LOEUF) genes are dosage-sensitive; knockdown may trigger "
        "broader compensatory transcriptomic responses. Multiplying by is_target restricts "
        "the effect to the targeted gene column."
    )
    inputs = ["control_cells", "gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # Load LOEUF per gene, mapped to ctx.gene_index
        loeuf = np.full(n_genes, np.nan, dtype=float)
        constraint = ctx.knowledge("gene_constraint")
        if constraint is not None:
            cols = constraint.get("columns", [])
            try:
                loeuf_col = cols.index("oe_lof_upper")
            except ValueError:
                loeuf_col = None
            genes_map = constraint.get("genes", {})
            if loeuf_col is not None and isinstance(genes_map, dict):
                for sym, vals in genes_map.items():
                    gi = ctx.gene_index.get(sym)
                    if gi is None or vals is None:
                        continue
                    if loeuf_col >= len(vals):
                        continue
                    v = vals[loeuf_col]
                    if v is None:
                        continue
                    try:
                        loeuf[gi] = float(v)
                    except (TypeError, ValueError):
                        continue

        # Fill missing LOEUF with the mean of available values (finite fallback)
        finite_mask = np.isfinite(loeuf)
        if finite_mask.any():
            fill = float(loeuf[finite_mask].mean())
            loeuf = np.where(finite_mask, loeuf, fill)
        else:
            loeuf = np.zeros(n_genes, dtype=float)

        for i, p in enumerate(perts):
            tgt = ctx.target_indices(p)
            if not tgt:
                continue
            vals = loeuf[tgt]
            # If multiple targets, average their LOEUF
            val = float(np.mean(vals)) if len(vals) > 0 else 0.0
            if not np.isfinite(val):
                val = 0.0
            for g in tgt:
                out[i, g, 0] = val

        return out
