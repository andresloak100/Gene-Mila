import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveTimesCpgPromoterE325(Feature):
    name = "additive_times_cpg_promoter_e325"
    version = 1
    description = "Elementwise product of additive_response and cpg_oe_promoter from gene_annotation."
    rationale = ("CpG promoter content influences gene regulation; interaction with additive_response "
                 "may improve predictions for genes with high or low CpG promoters.")
    inputs = ["gene_annotation", "additive_response"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        add = ctx.feature("additive_response", perts, params=None)
        add = np.asarray(add, dtype=float)
        if add.ndim == 2:
            add = add[:, :, None]

        cpg = np.zeros(n_genes, dtype=float)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes_map = ann.get("genes", {}) or {}
            columns = ann.get("columns", []) or []
            if "cpg_oe_promoter" in columns:
                idx = columns.index("cpg_oe_promoter")
            else:
                idx = None
            for g, gi in ctx.gene_index.items():
                vals = genes_map.get(g)
                if vals is None:
                    continue
                try:
                    v = vals[idx] if idx is not None else None
                except Exception:
                    v = None
                if v is None:
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv):
                    cpg[gi] = fv

        out = add * cpg[None, :, None]
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
