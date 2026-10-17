import numpy as np
from genemila.features.api import Feature, register


@register
class PairTargetConstraintAggregateE433(Feature):
    name = "pair_target_constraint_aggregate_e433"
    version = 1
    description = ("Aggregate LoF-intolerance scores of a perturbation's target genes "
                   "using min, max, or product; single targets use their own score.")
    rationale = ("The combined loss-of-function intolerance of both targets in a pair "
                 "may modulate the perturbation effect; different aggregations capture "
                 "essentiality differently.")
    inputs = ["knowledge"]
    params = {"aggregation": "min", "constraint_metric": "loeuf"}
    dim = 1

    def _score_table(self, ctx, params):
        key = ("pair_constraint_scores", params.get("constraint_metric", "loeuf"))
        cache = ctx.cache
        if key in cache:
            return cache[key]

        metric = params.get("constraint_metric", "loeuf")
        scores = np.full(ctx.n_genes, np.nan, dtype=float)

        kd = ctx.knowledge("gene_constraint")
        if kd is not None and isinstance(kd, dict):
            cols = kd.get("columns", [])
            genes = kd.get("genes", {})
            if metric == "loeuf":
                col = "oe_lof_upper"
            elif metric == "pli":
                col = "pLI"
            else:
                col = "oe_lof_upper"
            if col in cols:
                idx = cols.index(col)
                raw = {}
                for g, vals in genes.items():
                    if g not in ctx.gene_index or vals is None:
                        continue
                    try:
                        v = vals[idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        v = float(v)
                    except (TypeError, ValueError):
                        continue
                    if not np.isfinite(v):
                        continue
                    raw[g] = v

                if raw:
                    vals = np.array(list(raw.values()), dtype=float)
                    if metric == "loeuf":
                        # LOEUF: lower = more intolerant. Intolerance = 1 - normalized LOEUF
                        lo = np.nanpercentile(vals, 5)
                        hi = np.nanpercentile(vals, 95)
                        if hi <= lo:
                            hi = lo + 1e-6
                        for g, v in raw.items():
                            n = (v - lo) / (hi - lo)
                            n = min(max(n, 0.0), 1.0)
                            scores[ctx.gene_index[g]] = 1.0 - n
                    else:
                        # pLI: higher = more intolerant
                        for g, v in raw.items():
                            n = min(max(v, 0.0), 1.0)
                            scores[ctx.gene_index[g]] = n

        # Fill missing with neutral 0.0 (no intolerance info)
        scores = np.where(np.isfinite(scores), scores, 0.0)
        cache[key] = scores
        return scores

    def compute(self, ctx, perts, params):
        agg = params.get("aggregation", "min")
        scores = self._score_table(ctx, params)
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            tgs = ctx.target_genes(p)
            if not tgs:
                continue
            vals = []
            for g in tgs:
                gi = ctx.gene_index.get(g)
                if gi is not None:
                    vals.append(scores[gi])
            if not vals:
                continue
            vals = np.array(vals, dtype=float)
            if len(vals) == 1:
                s = float(vals[0])
            else:
                if agg == "min":
                    s = float(vals.min())
                elif agg == "max":
                    s = float(vals.max())
                elif agg == "product":
                    s = float(np.prod(vals))
                elif agg == "mean":
                    s = float(vals.mean())
                else:
                    s = float(vals.min())
            out[i, :, 0] = s

        out = np.where(np.isfinite(out), out, 0.0)
        return out
