import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveResponseXTargetConstraintV2(Feature):
    name = "additive_response_x_target_constraint_v2_e171"
    version = 1
    description = "additive_response multiplied by the mean normalized LoF-intolerance (-LOEUF) of the perturbation's target gene(s)."
    rationale = "Highly LoF-constrained targets may have tighter regulation, attenuating the additive downstream response; an interaction term captures this modulation."
    inputs = ["train_delta", "knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1))

        # Build a per-gene normalized LoF-intolerance score from gene_constraint.
        score = np.zeros(ctx.n_genes, dtype=float)
        cache = ctx.cache
        key = "_e171_loeuf_score"
        if key in cache:
            score = cache[key]
        else:
            kc = ctx.knowledge("gene_constraint")
            if kc is not None and "genes" in kc and "columns" in kc:
                cols = list(kc["columns"])
                if "oe_lof_upper" in cols:
                    j = cols.index("oe_lof_upper")
                    vals = np.full(ctx.n_genes, np.nan, dtype=float)
                    gtab = kc["genes"]
                    for g, gi in ctx.gene_index.items():
                        row = gtab.get(g)
                        if row is None:
                            continue
                        try:
                            v = row[j]
                        except (IndexError, TypeError):
                            continue
                        if v is None:
                            continue
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv):
                            vals[gi] = fv
                    # LoF-intolerance = -LOEUF (low LOEUF -> high intolerance).
                    raw = -vals
                    mask = np.isfinite(raw)
                    if mask.any():
                        mu = raw[mask].mean()
                        sd = raw[mask].std()
                        if sd > 1e-12:
                            z = (raw - mu) / sd
                        else:
                            z = raw - mu
                        z = np.where(mask, z, 0.0)
                        score = z
            cache[key] = score

        for i, p in enumerate(perts):
            tidx = ctx.target_indices(p)
            if len(tidx) == 0:
                tscore = 0.0
            else:
                tscore = float(np.mean(score[np.asarray(tidx, dtype=int)]))

            _, d = ctx.train_delta(exclude=p)
            add = d.mean(axis=0)
            out[i, :, 0] = add * tscore

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
