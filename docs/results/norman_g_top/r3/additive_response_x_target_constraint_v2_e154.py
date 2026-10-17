import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveResponseXTargetConstraintV2E154(Feature):
    name = "additive_response_x_target_constraint_v2_e154"
    version = 1
    description = "Product of additive_response and mean LoF-intolerance score of the perturbation target(s)."
    rationale = ("LoF-intolerant targets may have broader downstream effects; scaling the additive "
                 "response by target constraint refines the baseline.")
    inputs = ["knowledge", "feature"]
    params = {}
    dim = 1

    def _constraint_scores(self, ctx, params):
        cache = ctx.cache
        key = "e154_constraint_scores"
        if key in cache:
            return cache[key]
        scores = {}
        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            genes = kc.get("genes", {})
            cols = kc.get("columns", [])
            idx = {c: i for i, c in enumerate(cols)}
            i_loeuf = idx.get("oe_lof_upper", None)
            i_pli = idx.get("pLI", None)
            for g, vals in genes.items():
                if vals is None:
                    continue
                s = None
                if i_loeuf is not None and i_loeuf < len(vals) and vals[i_loeuf] is not None:
                    try:
                        s = 1.0 - float(vals[i_loeuf])
                    except (TypeError, ValueError):
                        s = None
                if s is None and i_pli is not None and i_pli < len(vals) and vals[i_pli] is not None:
                    try:
                        s = float(vals[i_pli])
                    except (TypeError, ValueError):
                        s = None
                if s is not None and np.isfinite(s):
                    scores[g] = s
        cache[key] = scores
        return scores

    def compute(self, ctx, perts, params):
        scores = self._constraint_scores(ctx, params)
        add = ctx.feature("additive_response", perts)
        add = np.asarray(add, dtype=float)
        if add.ndim == 2:
            add = add[:, :, None]
        out = np.zeros((len(perts), ctx.n_genes, 1))
        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            vals = [scores[g] for g in tg if g in scores]
            if vals:
                avg = float(np.mean(vals))
            else:
                avg = 0.0
            out[i, :, 0] = add[i, :, 0] * avg
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
