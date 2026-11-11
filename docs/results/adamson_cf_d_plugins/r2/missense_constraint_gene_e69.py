import numpy as np
from genemila.features.api import Feature, register


@register
class MissenseConstraintGeneE69(Feature):
    name = "missense_constraint_gene_e69"
    version = 1
    description = "Standardized per-gene missense constraint (pRec or mis_z) from gene_constraint."
    rationale = "Missense-intolerant genes are under stronger purifying selection and may show larger or more coherent expression changes when perturbed."
    inputs = ["gene_constraint"]
    params = {"column": "pRec"}
    dim = 1

    def compute(self, ctx, perts, params):
        col = params.get("column", "pRec")
        out = np.zeros((len(perts), ctx.n_genes, 1))

        cache_key = ("missense_constraint_gene_e69", col)
        if cache_key in ctx.cache:
            vec = ctx.cache[cache_key]
        else:
            vec = np.zeros(ctx.n_genes, dtype=float)
            kc = ctx.knowledge("gene_constraint")
            if kc is not None:
                columns = kc.get("columns", [])
                genes = kc.get("genes", {})
                if col in columns:
                    ci = columns.index(col)
                    for g, vals in genes.items():
                        gi = ctx.gene_index.get(g)
                        if gi is None:
                            continue
                        if vals is None or ci >= len(vals):
                            continue
                        v = vals[ci]
                        if v is None:
                            continue
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv):
                            vec[gi] = fv
            mu = vec.mean()
            sd = vec.std()
            if sd > 0 and np.isfinite(sd):
                vec = (vec - mu) / sd
            else:
                vec = vec - mu
            vec = np.where(np.isfinite(vec), vec, 0.0)
            ctx.cache[cache_key] = vec

        out[:, :, 0] = vec[None, :]
        return out
