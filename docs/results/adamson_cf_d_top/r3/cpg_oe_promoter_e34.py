import numpy as np
from genemila.features.api import Feature, register

@register
class CpGOePromoterE34(Feature):
    name = "cpg_oe_promoter_e34"
    version = 1
    description = "Observed/expected CpG ratio in promoter for gene g (gene_annotation.cpg_oe_promoter), median-imputed."
    rationale = "High CpG promoters mark poised/dynamically regulated genes that respond more strongly to perturbations."
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        vals = np.full(n_genes, np.nan, dtype=np.float64)

        ann = ctx.knowledge("gene_annotation")
        if ann is not None and isinstance(ann, dict):
            genes = ann.get("genes")
            columns = ann.get("columns")
            if isinstance(genes, dict) and isinstance(columns, list):
                if "cpg_oe_promoter" in columns:
                    col = columns.index("cpg_oe_promoter")
                    for g, gi in ctx.gene_index.items():
                        row = genes.get(g)
                        if row is None:
                            continue
                        try:
                            v = row[col]
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

        finite = np.isfinite(vals)
        if finite.any():
            med = float(np.median(vals[finite]))
        else:
            med = 0.0
        vals[~finite] = med

        out = np.empty((len(perts), n_genes, 1), dtype=np.float64)
        out[:, :, 0] = vals[None, :]
        out[~np.isfinite(out)] = med
        return out
