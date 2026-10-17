import numpy as np
from genemila.features.api import Feature, register


@register
class TargetConstraintInteraction(Feature):
    name = "target_constraint_interaction_e553"
    version = 1
    description = ("Interaction of target gene(s) LOEUF constraint with gene g's own "
                   "LOEUF constraint, via product or min.")
    rationale = ("LOEUF reflects dosage sensitivity; activating a constrained target "
                 "may produce stronger downstream effects, modulated by g's own constraint.")
    inputs = ["knowledge", "control_mean"]
    params = {"mode": "product"}
    dim = 1

    def _get_loeuf(self, ctx):
        cached = ctx.cache.get("_loeuf_e553")
        if cached is not None:
            return cached
        loeuf = np.full(ctx.n_genes, np.nan, dtype=float)
        kn = ctx.knowledge("gene_constraint")
        if kn is not None:
            cols = kn.get("columns", [])
            try:
                idx = cols.index("oe_lof_upper")
            except ValueError:
                idx = None
            genes = kn.get("genes", {})
            if idx is not None:
                for g, gi in ctx.gene_index.items():
                    vals = genes.get(g)
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
                        loeuf[gi] = fv
        # Fill missing with the median of observed values (neutral fallback).
        obs = loeuf[np.isfinite(loeuf)]
        fill = float(np.median(obs)) if obs.size > 0 else 1.0
        loeuf = np.where(np.isfinite(loeuf), loeuf, fill)
        # Clip to a sensible positive range.
        loeuf = np.clip(loeuf, 1e-3, None)
        ctx.cache["_loeuf_e553"] = loeuf
        return loeuf

    def compute(self, ctx, perts, params):
        mode = params.get("mode", "product")
        loeuf = self._get_loeuf(ctx)
        # Constraint score: higher = more constrained (low LOEUF).
        cons = 1.0 / loeuf  # inverse LOEUF, positive
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if not t_idx:
                # No measured target: neutral value.
                out[i, :, 0] = 0.0
                continue
            t_cons = cons[np.asarray(t_idx, dtype=int)]
            if mode == "min":
                # min of LOEUF => max of constraint; combine target constraint with g's.
                t_val = t_cons.max()  # most constrained target
                out[i, :, 0] = np.minimum(t_val, cons)
            else:  # product
                t_val = float(t_cons.mean())
                out[i, :, 0] = t_val * cons
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
