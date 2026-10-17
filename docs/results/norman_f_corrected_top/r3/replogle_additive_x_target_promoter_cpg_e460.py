import numpy as np
from genemila.features.api import Feature, register


@register
class ReplogleAdditiveXTargetPromoterCpgE460(Feature):
    name = "replogle_additive_x_target_promoter_cpg_e460"
    version = 1
    description = ("Product of sign-corrected Replogle additive response and the mean "
                   "CpG observed/expected ratio in promoters of the perturbation's target genes.")
    rationale = ("CpG islands mark active chromatin and CRISPRa efficacy; targets with high "
                 "promoter CpG density may be more responsive to activation, amplifying the "
                 "sign-corrected Replogle additive response.")
    inputs = ["train_delta", "knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        # CpG observed/expected in promoter per gene
        cpg = np.zeros(ctx.n_genes, dtype=float)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            cols = ann.get("columns", [])
            try:
                ci = cols.index("cpg_oe_promoter")
            except ValueError:
                ci = None
            genes_ann = ann.get("genes", {})
            if ci is not None:
                for g, vals in genes_ann.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None or vals is None:
                        continue
                    v = vals[ci]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        cpg[gi] = fv

        # Replogle sign-corrected additive response, memoised per perturbation
        cache = ctx.cache
        if "repl_genes" not in cache:
            rk = ctx.knowledge("replogle2022_k562")
            if rk is None:
                cache["repl_genes"] = None
                cache["repl_delta"] = None
                cache["repl_sign"] = -1.0
            else:
                cache["repl_genes"] = rk.get("genes")
                cache["repl_delta"] = rk.get("perts")
                cache["repl_sign"] = float(rk.get("sign", -1.0))
        repl_genes = cache["repl_genes"]
        repl_delta = cache["repl_delta"]
        repl_sign = cache["repl_sign"]

        def replogle_additive(p):
            if repl_genes is None or repl_delta is None:
                return None
            tg = ctx.target_genes(p)
            if not tg:
                return None
            acc = np.zeros(ctx.n_genes, dtype=float)
            for t in tg:
                entry = repl_delta.get(t)
                if entry is None:
                    return None
                if isinstance(entry, dict):
                    d = entry.get("delta")
                else:
                    d = entry
                if d is None:
                    return None
                d = np.asarray(d, dtype=float)
                if d.shape[0] < ctx.n_genes:
                    return None
                acc += repl_sign * d[:ctx.n_genes]
            return acc

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            if tg:
                idxs = [ctx.gene_index[g] for g in tg if g in ctx.gene_index]
                if idxs:
                    mean_cpg = float(np.mean(cpg[idxs]))
                else:
                    mean_cpg = 0.0
            else:
                mean_cpg = 0.0

            add = replogle_additive(p)
            if add is None:
                continue
            out[i, :, 0] = add * mean_cpg

        out[~np.isfinite(out)] = 0.0
        return out
