import numpy as np
from genemila.features.api import Feature, register


@register
class TargetPromoterCpGMean(Feature):
    name = "target_promoter_cpg_mean_e521"
    version = 1
    description = "Mean cpg_oe_promoter across p's target genes."
    rationale = ("Perturbation targets with high promoter CpG content may produce larger "
                 "expression changes due to stronger CRISPRa binding.")
    inputs = ["knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        ann = ctx.knowledge("gene_annotation")
        out = np.zeros((len(perts), ctx.n_genes, 1))

        genes = None
        col = None
        if ann is not None:
            genes = ann.get("genes")
            columns = ann.get("columns") or []
            if "cpg_oe_promoter" in columns:
                col = columns.index("cpg_oe_promoter")

        if genes is None or col is None:
            return out

        # Precompute per-gene value once.
        cache = ctx.cache
        key = "_e521_gene_vals"
        if key not in cache:
            vals = np.full(ctx.n_genes, np.nan, dtype=np.float64)
            for g, gi in ctx.gene_index.items():
                rec = genes.get(g)
                if rec is None:
                    continue
                try:
                    v = rec[col]
                except (TypeError, IndexError):
                    continue
                if v is None:
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv):
                    vals[gi] = fv
            cache[key] = vals

        gene_vals = cache[key]

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            if not tg:
                continue
            acc = 0.0
            cnt = 0
            for g in tg:
                gi = ctx.gene_index.get(g)
                if gi is None:
                    continue
                v = gene_vals[gi]
                if np.isfinite(v):
                    acc += v
                    cnt += 1
            if cnt > 0:
                out[i, :, 0] = acc / cnt

        return out
