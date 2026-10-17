import numpy as np
from genemila.features.api import Feature, register


@register
class PairTargetLofIntolerance(Feature):
    name = "pair_target_lof_intolerance_e253"
    version = 1
    description = "Aggregate LOEUF (LoF intolerance) of a perturbation's target gene(s)."
    rationale = ("For pair perturbations the combined LoF intolerance of both targets "
                 "(e.g. mean LOEUF) may predict the strength of the response; for a "
                 "single perturbation the target's own LOEUF is used.")
    inputs = ["control_cells"]
    params = {"aggregation": "mean"}
    dim = 1

    def _load_loeuf(self, ctx):
        cache = ctx.cache
        key = "__loeuf_map_e253"
        if key in cache:
            return cache[key]
        loeuf = {}
        ann = ctx.knowledge("gene_constraint")
        if ann is not None:
            cols = ann.get("columns", [])
            genes = ann.get("genes", {})
            idx = None
            for j, c in enumerate(cols):
                if c == "oe_lof_upper":
                    idx = j
                    break
            if idx is not None:
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
                        loeuf[g] = fv
        cache[key] = loeuf
        return loeuf

    def _global_mean(self, loeuf):
        if not loeuf:
            return 0.0
        return float(np.mean(list(loeuf.values())))

    def compute(self, ctx, perts, params):
        agg = str(params.get("aggregation", "mean")).lower()
        loeuf = self._load_loeuf(ctx)
        gmean = self._global_mean(loeuf)
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            vals = [loeuf[g] for g in tg if g in loeuf]
            if len(vals) == 0:
                score = gmean
            elif agg == "min":
                score = float(np.min(vals))
            elif agg == "max":
                score = float(np.max(vals))
            else:
                score = float(np.mean(vals))
            if not np.isfinite(score):
                score = gmean
            out[i, :, 0] = score

        return out
