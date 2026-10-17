import numpy as np
from genemila.features.api import Feature, register


@register
class GenePromoterCpGIslandE642(Feature):
    name = "gene_promoter_cpg_island_e642"
    version = 1
    description = "Binary flag: 1 if gene g has a CpG island promoter (cpg_oe_promoter > threshold)."
    rationale = ("Promoter CpG islands distinguish housekeeping from regulated genes; "
                 "a pure gene-level flag may add predictive power independent of target identity.")
    inputs = ["knowledge:gene_annotation"]
    params = {"threshold": 0.6}
    dim = 1

    def compute(self, ctx, perts, params):
        threshold = float(params.get("threshold", 0.6))
        n_genes = ctx.n_genes
        flag = np.zeros(n_genes, dtype=np.float64)

        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes_dict = ann.get("genes", {}) if isinstance(ann, dict) else {}
            cols = ann.get("columns", []) if isinstance(ann, dict) else []
            try:
                col_idx = list(cols).index("cpg_oe_promoter")
            except (ValueError, TypeError):
                col_idx = None
            if col_idx is not None and genes_dict:
                for g, col in ctx.gene_index.items():
                    vals = genes_dict.get(g)
                    if vals is None:
                        continue
                    if col_idx >= len(vals):
                        continue
                    v = vals[col_idx]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if not np.isfinite(fv):
                        continue
                    if fv > threshold:
                        flag[col] = 1.0

        out = np.broadcast_to(flag[None, :, None], (len(perts), n_genes, 1)).copy()
        return out
