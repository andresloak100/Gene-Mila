import numpy as np
from genemila.features.api import Feature, FeatureContext, register


@register
class ReplogleAdditiveXPromoterCpgOe(Feature):
    name = "replogle_additive_x_promoter_cpg_oe_e391"
    version = 1
    description = "Product of sign-corrected Replogle additive response and gene g's promoter CpG observed/expected ratio from gene_annotation."
    rationale = "Promoter CpG O/E ratio reflects chromatin state and can influence how strongly CRISPRa perturbations propagate to downstream genes."
    inputs = ["knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx: FeatureContext, perts: list[str], params: dict) -> np.ndarray:
        n = ctx.n_genes
        ann = ctx.knowledge("gene_annotation")
        cpg = np.ones(n, dtype=np.float64)
        if ann is not None:
            genes_ann = ann.get("genes", {})
            cols = ann.get("columns", [])
            if "cpg_oe_promoter" in cols:
                ci = cols.index("cpg_oe_promoter")
            else:
                ci = None
            if ci is not None:
                for g, gi in ctx.gene_index.items():
                    vals = genes_ann.get(g)
                    if vals is not None and ci < len(vals):
                        v = vals[ci]
                        if v is not None:
                            cpg[gi] = float(v)
        cpg = np.nan_to_num(cpg, nan=1.0, posinf=1.0, neginf=1.0)

        out = np.zeros((len(perts), n, 1), dtype=np.float64)
        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            add = d.mean(axis=0)
            out[i, :, 0] = add * cpg
        return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
