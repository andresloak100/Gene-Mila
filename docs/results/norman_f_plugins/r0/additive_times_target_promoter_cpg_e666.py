import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveTimesTargetPromoterCpg(Feature):
    name = "additive_times_target_promoter_cpg_e666"
    version = 1
    description = "additive_response times the mean promoter CpG observed/expected ratio over the perturbation's target genes."
    rationale = "CRISPRa efficacy depends on promoter CpG content; high-CpG promoters may be more easily activated, so the additive response should be scaled by target promoter CpG content."
    inputs = ["gene_annotation", "additive_response"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        ann = ctx.knowledge("gene_annotation")
        genes = ann.get("genes", {}) if ann else {}
        columns = ann.get("columns", []) if ann else []
        try:
            cpg_col = columns.index("cpg_oe_promoter")
        except ValueError:
            cpg_col = None

        # per-gene cpg value
        cpg_gene = np.full(n_genes, np.nan)
        if cpg_col is not None:
            for i, g in enumerate(ctx.genes):
                vals = genes.get(g)
                if vals is not None and cpg_col < len(vals):
                    v = vals[cpg_col]
                    if v is not None:
                        try:
                            fv = float(v)
                            if np.isfinite(fv):
                                cpg_gene[i] = fv
                        except (TypeError, ValueError):
                            pass

        # additive_response feature (len(perts), n_genes, 1)
        add = ctx.feature("additive_response", perts, params=None)
        add = np.asarray(add, dtype=float)
        if add.ndim == 2:
            add = add[:, :, None]

        # precompute mean target cpg per perturbation
        mean_cpg = np.zeros(len(perts))
        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            vals = []
            for tg in tgenes:
                gi = ctx.gene_index.get(tg)
                if gi is not None and np.isfinite(cpg_gene[gi]):
                    vals.append(cpg_gene[gi])
            mean_cpg[i] = float(np.mean(vals)) if vals else 0.0

        out[:, :, 0] = add[:, :, 0] * mean_cpg[:, None]
        out[~np.isfinite(out)] = 0.0
        return out
