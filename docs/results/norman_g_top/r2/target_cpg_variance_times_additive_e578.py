import numpy as np
from genemila.features.api import Feature, register


@register
class TargetCpgVarianceTimesAdditiveE578(Feature):
    name = "target_cpg_variance_times_additive_e578"
    version = 1
    description = ("For perturbation p, variance of cpg_oe_promoter across its target genes, "
                   "multiplied by additive_response.")
    rationale = ("Heterogeneous promoter CpG content across targets may indicate diverse "
                 "regulation, affecting response magnitude.")
    inputs = ["gene_annotation", "additive_response"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        # Load annotation once.
        ann = ctx.knowledge("gene_annotation")
        cache = ctx.cache
        if "cpg_oe_promoter" not in cache:
            cpg = {}
            if ann is not None:
                cols = ann.get("columns", [])
                genes_tbl = ann.get("genes", {}) or {}
                if "cpg_oe_promoter" in cols:
                    idx = cols.index("cpg_oe_promoter")
                    for g, vals in genes_tbl.items():
                        if vals is None:
                            continue
                        try:
                            v = vals[idx]
                        except (IndexError, TypeError):
                            continue
                        if v is None:
                            continue
                        try:
                            cpg[g] = float(v)
                        except (TypeError, ValueError):
                            continue
            cache["cpg_oe_promoter"] = cpg
        cpg = cache["cpg_oe_promoter"]

        # additive_response feature (dim 1): (n_perts, n_genes, 1)
        add = ctx.feature("additive_response", perts, None)
        if add.ndim == 2:
            add = add[:, :, None]

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            vals = [cpg[g] for g in tg if g in cpg]
            if len(vals) >= 2:
                var = float(np.var(np.asarray(vals, dtype=float)))
            else:
                var = 0.0
            out[i, :, 0] = var * add[i, :, 0]

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
