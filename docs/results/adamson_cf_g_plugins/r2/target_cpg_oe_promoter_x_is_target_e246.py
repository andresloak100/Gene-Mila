import numpy as np
from genemila.features.api import Feature, register


@register
class TargetCpGOePromoterXIsTarget(Feature):
    name = "target_cpg_oe_promoter_x_is_target_e246"
    version = 1
    description = "Product of target gene's cpg_oe_promoter and is_target indicator."
    rationale = (
        "CpG observed/expected ratio in the target gene's promoter may modulate "
        "the perturbation response; interacting it with the is_target indicator "
        "lets the model scale target-specific effects by promoter CpG content."
    )
    inputs = ["knowledge:gene_annotation", "target_indices"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        cpg_values = None
        if ann is not None:
            cols = ann.get("columns", [])
            genes = ann.get("genes", {})
            if "cpg_oe_promoter" in cols:
                col_idx = cols.index("cpg_oe_promoter")
                cpg_values = np.full(n_genes, np.nan, dtype=float)
                for g in ctx.genes:
                    vals = genes.get(g)
                    if vals is None:
                        continue
                    v = vals[col_idx]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        cpg_values[ctx.gene_index[g]] = fv

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            if cpg_values is None:
                # Fall back to 1.0 so the feature degenerates to is_target.
                vals = np.ones(len(tgt_idx), dtype=float)
            else:
                vals = cpg_values[tgt_idx]
                vals = np.where(np.isfinite(vals), vals, 0.0)
            out[i, tgt_idx, 0] = vals

        return out
