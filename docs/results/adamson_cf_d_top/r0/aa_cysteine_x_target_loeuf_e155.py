import numpy as np
from genemila.features.api import Feature, register

@register
class AaCysteineXTargetLoeuf(Feature):
    name = "aa_cysteine_x_target_loeuf_e155"
    version = 1
    description = "Product of gene g's cysteine fraction (aa_C) and the target's LOEUF (oe_lof_upper)."
    rationale = "Cysteine-rich proteins may be sensitive to stress pathways induced by perturbing intolerant targets."
    inputs = ["gene_annotation", "gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        ann = ctx.knowledge("gene_annotation")
        cons = ctx.knowledge("gene_constraint")

        aa_c = np.full(n_genes, np.nan)
        loeuf = np.full(n_genes, np.nan)

        if ann is not None:
            genes_ann = ann.get("genes", {})
            cols = ann.get("columns", [])
            if "aa_C" in cols:
                idx = cols.index("aa_C")
                for gi, g in enumerate(ctx.genes):
                    v = genes_ann.get(g)
                    if v is not None and len(v) > idx and v[idx] is not None:
                        aa_c[gi] = float(v[idx])

        if cons is not None:
            genes_cons = cons.get("genes", {})
            cols = cons.get("columns", [])
            if "oe_lof_upper" in cols:
                idx = cols.index("oe_lof_upper")
                for gi, g in enumerate(ctx.genes):
                    v = genes_cons.get(g)
                    if v is not None and len(v) > idx and v[idx] is not None:
                        loeuf[gi] = float(v[idx])

        aa_c = np.nan_to_num(aa_c, nan=0.0)
        loeuf = np.nan_to_num(loeuf, nan=0.0)

        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if len(t_idx) == 0:
                t_val = 0.0
            else:
                vals = loeuf[t_idx]
                t_val = float(np.nanmean(vals)) if len(vals) > 0 else 0.0
            out[i, :, 0] = aa_c * t_val

        return out
