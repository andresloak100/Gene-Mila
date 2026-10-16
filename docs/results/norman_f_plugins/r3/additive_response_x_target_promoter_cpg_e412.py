import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveResponseXTargetPromoterCpG(Feature):
    name = "additive_response_x_target_promoter_cpg_e412"
    version = 1
    description = "Product of additive_response and the mean promoter CpG observed/expected ratio across target genes of p."
    rationale = ("CRISPRa efficiency depends on target-site accessibility; promoter CpG content is a "
                 "proxy for open chromatin. Scaling the additive response by the mean target promoter "
                 "CpG o/e ratio modulates predicted effect strength by activation efficiency.")
    inputs = ["gene_annotation", "target_genes"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        # additive response baseline
        add = ctx.feature("additive_response", perts)
        if add.ndim == 3:
            add = add[:, :, 0]
        elif add.ndim == 2:
            add = add

        # fetch gene annotation for cpg_oe_promoter
        ann = ctx.knowledge("gene_annotation") or {}
        genes_ann = ann.get("genes", {}) if isinstance(ann, dict) else {}
        columns = ann.get("columns", []) if isinstance(ann, dict) else []
        try:
            cpg_idx = columns.index("cpg_oe_promoter")
        except ValueError:
            cpg_idx = None

        # cache per-gene cpg values
        cache = ctx.cache
        cpg_key = "cpg_oe_promoter_vec"
        if cpg_key not in cache:
            vec = np.full(n_genes, np.nan, dtype=float)
            if cpg_idx is not None:
                for gi, g in enumerate(ctx.genes):
                    vals = genes_ann.get(g)
                    if vals is None:
                        continue
                    try:
                        v = vals[cpg_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        vec[gi] = fv
            cache[cpg_key] = vec
        cpg_vec = cache[cpg_key]

        # global mean of finite cpg values as fallback
        finite = cpg_vec[np.isfinite(cpg_vec)]
        global_mean = float(finite.mean()) if finite.size > 0 else 0.0

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            idxs = [ctx.gene_index[g] for g in tgenes if g in ctx.gene_index]
            if len(idxs) == 0:
                mean_cpg = global_mean
            else:
                vals = cpg_vec[idxs]
                ok = vals[np.isfinite(vals)]
                mean_cpg = float(ok.mean()) if ok.size > 0 else global_mean
            out[i, :, 0] = add[i] * mean_cpg

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
