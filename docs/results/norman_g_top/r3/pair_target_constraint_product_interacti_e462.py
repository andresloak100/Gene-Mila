import numpy as np
from genemila.features.api import Feature, register


@register
class PairTargetConstraintProductInteractionE462(Feature):
    name = "pair_target_constraint_product_interacti_e462"
    version = 1
    description = ("For pair perturbations, product of normalized LoF-intolerance scores "
                   "of the two target genes; 0 for single perturbations.")
    rationale = ("Pairs of LoF-intolerant genes may show synergistic effects; the product "
                 "captures nonlinear combined constraint beyond additive contributions.")
    inputs = ["target_genes", "knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))

        # Load LOEUF-based LoF-intolerance scores once.
        cache = ctx.cache
        key = "_e462_lof_intolerance"
        if key in cache:
            lof = cache[key]
        else:
            lof = np.full(ctx.n_genes, np.nan)
            kd = ctx.knowledge("gene_constraint")
            if kd is not None:
                genes = kd.get("genes", {})
                cols = kd.get("columns", [])
                try:
                    loeuf_idx = cols.index("oe_lof_upper")
                except ValueError:
                    loeuf_idx = None
                if loeuf_idx is not None:
                    for g, vals in genes.items():
                        gi = ctx.gene_index.get(g)
                        if gi is None or vals is None:
                            continue
                        try:
                            v = vals[loeuf_idx]
                        except (IndexError, TypeError):
                            continue
                        if v is None:
                            continue
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv):
                            lof[gi] = fv
            # Normalize (1 - LOEUF) to [0, 1] over the finite values.
            score = np.zeros(ctx.n_genes)
            finite = np.isfinite(lof)
            if finite.any():
                intol = 1.0 - lof[finite]
                lo = intol.min()
                hi = intol.max()
                if hi > lo:
                    intol = (intol - lo) / (hi - lo)
                else:
                    intol = np.full_like(intol, 0.5)
                score[finite] = intol
            else:
                score[:] = 0.0
            cache[key] = score
            lof = score

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            if tg is None or len(tg) != 2:
                continue
            idxs = [ctx.gene_index[g] for g in tg if g in ctx.gene_index]
            if len(idxs) != 2:
                continue
            prod = float(lof[idxs[0]]) * float(lof[idxs[1]])
            out[i, :, 0] = prod

        out[~np.isfinite(out)] = 0.0
        return out
