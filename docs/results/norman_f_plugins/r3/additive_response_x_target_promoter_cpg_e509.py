import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveResponseXTargetPromoterCpgE509(Feature):
    name = "additive_response_x_target_promoter_cpg_e509"
    version = 1
    description = ("Product of the additive baseline prediction and the mean promoter CpG "
                   "observed/expected ratio across the target genes of p.")
    rationale = ("CRISPRa efficiency may depend on target promoter CpG content; high-CpG "
                 "promoters may be more activatable, modulating the additive response.")
    inputs = ["train_delta", "gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))

        # --- additive baseline (leave-one-out mean delta) ---
        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            out[i, :, 0] = d.mean(axis=0)

        # --- promoter CpG observed/expected per gene ---
        ann = ctx.knowledge("gene_annotation")
        cpg_col = None
        if ann is not None:
            cols = ann.get("columns", [])
            for j, c in enumerate(cols):
                if c == "cpg_oe_promoter":
                    cpg_col = j
                    break
        cpg_vals = np.full(ctx.n_genes, np.nan)
        if ann is not None and cpg_col is not None:
            genes_dict = ann.get("genes", {})
            for g, idx in ctx.gene_index.items():
                v = genes_dict.get(g)
                if v is not None and cpg_col < len(v):
                    x = v[cpg_col]
                    if x is not None:
                        cpg_vals[idx] = float(x)

        # --- mean CpG over target genes of p ---
        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            vals = []
            for g in tg:
                gi = ctx.gene_index.get(g)
                if gi is not None:
                    v = cpg_vals[gi]
                    if np.isfinite(v):
                        vals.append(v)
            if vals:
                mean_cpg = float(np.mean(vals))
            else:
                mean_cpg = 0.0
            out[i, :, 0] *= mean_cpg

        # ensure finite
        out[~np.isfinite(out)] = 0.0
        return out
