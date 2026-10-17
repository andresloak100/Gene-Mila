import numpy as np
from genemila.features.api import Feature, register


@register
class LoeufTargetGeneInteraction(Feature):
    name = "loeuf_target_gene_interaction_e641"
    version = 1
    description = "For each (p,g), (1 - LOEUF_target) * (1 - LOEUF_gene)."
    rationale = (
        "Both target and gene essentiality may modulate response; their "
        "interaction captures synergistic essentiality effects."
    )
    inputs = ["gene_constraint", "target_genes"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))

        # Build per-gene LOEUF array with a median fallback for missing values.
        loeuf_gene = np.full(ctx.n_genes, np.nan, dtype=float)
        gc = ctx.knowledge("gene_constraint")
        if gc is not None:
            genes_tbl = gc.get("genes", {})
            cols = gc.get("columns", [])
            try:
                loeuf_idx = cols.index("oe_lof_upper")
            except ValueError:
                loeuf_idx = None
            if loeuf_idx is not None:
                for sym, vals in genes_tbl.items():
                    gi = ctx.gene_index.get(sym)
                    if gi is None:
                        continue
                    if vals is None:
                        continue
                    try:
                        v = vals[loeuf_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        loeuf_gene[gi] = fv

        finite_mask = np.isfinite(loeuf_gene)
        if finite_mask.any():
            default = float(np.median(loeuf_gene[finite_mask]))
        else:
            default = 1.0
        loeuf_gene = np.where(finite_mask, loeuf_gene, default)

        # (1 - LOEUF_gene) per gene, shape (n_genes,)
        gene_factor = 1.0 - loeuf_gene

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            loeuf_vals = []
            for sym in tg:
                gi = ctx.gene_index.get(sym)
                if gi is not None and np.isfinite(loeuf_gene[gi]):
                    loeuf_vals.append(loeuf_gene[gi])
            if loeuf_vals:
                loeuf_t = float(np.mean(loeuf_vals))
            else:
                loeuf_t = default
            target_factor = 1.0 - loeuf_t
            out[i, :, 0] = target_factor * gene_factor

        return out
