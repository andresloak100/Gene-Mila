import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveResponseXTargetConstraintE81(Feature):
    name = "additive_response_x_target_constraint_e81"
    version = 1
    description = ("Product of the additive_response feature and the mean LOEUF "
                   "(or pLI) constraint of perturbation p's target genes.")
    rationale = ("The effect of a perturbation may scale with the loss-of-function "
                 "intolerance of its target genes; multiplying the additive baseline "
                 "by a per-target constraint score lets the model modulate response "
                 "magnitude by target constraint.")
    inputs = ["feature", "knowledge"]
    params = {"constraint_metric": "oe_lof_upper"}
    dim = 1

    def compute(self, ctx, perts, params):
        metric = params.get("constraint_metric", "oe_lof_upper")

        # Get additive_response baseline (n_perts, n_genes, dim)
        base = ctx.feature("additive_response", perts)
        base = np.asarray(base, dtype=float)
        if base.ndim == 2:
            base = base[:, :, None]
        base = np.where(np.isfinite(base), base, 0.0)

        # Parse constraint knowledge once
        cache = ctx.cache
        key = ("e81_constraint", metric)
        if key not in cache:
            data = ctx.knowledge("gene_constraint")
            scores = {}
            if data is not None:
                genes = data.get("genes", {})
                cols = data.get("columns", [])
                if metric in cols:
                    idx = cols.index(metric)
                    for g, vals in genes.items():
                        if vals is None:
                            continue
                        try:
                            v = vals[idx]
                        except (IndexError, TypeError):
                            continue
                        if v is None:
                            continue
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv):
                            scores[g] = fv
            cache[key] = scores
        scores = cache[key]

        # Global fallback: mean of available finite scores
        if len(scores) > 0:
            fallback = float(np.mean(list(scores.values())))
        else:
            fallback = 0.0

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            vals = [scores[g] for g in tg if g in scores]
            if len(vals) > 0:
                c = float(np.mean(vals))
            else:
                c = fallback
            if not np.isfinite(c):
                c = 0.0
            out[i, :, 0] = base[i, :, 0] * c

        out = np.where(np.isfinite(out), out, 0.0)
        return out
