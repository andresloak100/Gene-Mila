import numpy as np
from genemila.features.api import Feature, register


@register
class CpgIslandPromoterGeneE116E132(Feature):
    name = "cpg_island_promoter_gene_e116_e132"
    version = 1
    description = ("Binary feature: 1 if gene g's promoter has high GC content and high "
                   "CpG observed/expected ratio (indicative of a CpG island), else 0.")
    rationale = ("CpG island promoters are associated with housekeeping genes and stable "
                 "expression, reducing the magnitude of perturbation-induced changes.")
    inputs = ["gene_annotation"]
    params = {"gc_threshold": 0.55, "cpg_oe_threshold": 0.6}
    dim = 1

    def compute(self, ctx, perts, params):
        gc_thr = float(params.get("gc_threshold", 0.55))
        oe_thr = float(params.get("cpg_oe_threshold", 0.6))

        ann = ctx.knowledge("gene_annotation")
        cols = ann.get("columns", []) if isinstance(ann, dict) else []
        genes_tbl = ann.get("genes", {}) if isinstance(ann, dict) else {}

        try:
            gc_idx = cols.index("gc_promoter")
        except ValueError:
            gc_idx = None
        try:
            oe_idx = cols.index("cpg_oe_promoter")
        except ValueError:
            oe_idx = None

        gene_flag = np.zeros(ctx.n_genes, dtype=float)
        if gc_idx is not None and oe_idx is not None:
            for gi, g in enumerate(ctx.genes):
                vals = genes_tbl.get(g)
                if vals is None:
                    continue
                try:
                    gc = vals[gc_idx]
                    oe = vals[oe_idx]
                except (IndexError, TypeError):
                    continue
                if gc is None or oe is None:
                    continue
                try:
                    gc = float(gc)
                    oe = float(oe)
                except (TypeError, ValueError):
                    continue
                if not np.isfinite(gc) or not np.isfinite(oe):
                    continue
                if gc > gc_thr and oe > oe_thr:
                    gene_flag[gi] = 1.0

        out = np.broadcast_to(gene_flag[None, :, None],
                              (len(perts), ctx.n_genes, 1)).astype(float).copy()
        return out
