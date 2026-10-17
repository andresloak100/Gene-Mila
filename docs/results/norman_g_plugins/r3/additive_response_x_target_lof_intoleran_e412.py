import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveResponseXTargetLofIntolerance(Feature):
    name = "additive_response_x_target_lof_intoleran_e412"
    version = 1
    description = ("Multiply the additive baseline prediction by a normalized LoF-intolerance "
                   "score of the perturbation's target gene(s).")
    rationale = ("LoF-intolerant (essential) targets may cause broader transcriptomic changes when "
                 "perturbed, so the additive response should be amplified for them.")
    inputs = ["gene_constraint", "target_genes", "train_delta"]
    params = {"score_column": "oe_lof_upper", "pair_aggregation": "mean"}
    dim = 1

    def _target_scores(self, ctx, params):
        """Return dict gene -> normalized LoF-intolerance in [0,1] (nan if unknown)."""
        cache = ctx.cache
        col = params.get("score_column", "oe_lof_upper")
        key = ("lof_scores", col)
        if key in cache:
            return cache[key]

        scores = {}
        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            genes_tbl = kc.get("genes", {})
            columns = kc.get("columns", [])
            try:
                ci = columns.index(col)
            except (ValueError, AttributeError):
                ci = None
            if ci is not None:
                raw = {}
                for g, vals in genes_tbl.items():
                    if vals is None:
                        continue
                    try:
                        v = vals[ci]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        v = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(v):
                        raw[g] = v
                if raw:
                    arr = np.array(list(raw.values()), dtype=float)
                    lo, hi = np.min(arr), np.max(arr)
                    span = hi - lo
                    for g, v in raw.items():
                        if span > 0:
                            norm = (v - lo) / span
                        else:
                            norm = 0.5
                        # LoF-intolerance: low LOEUF = intolerant -> invert
                        scores[g] = float(1.0 - norm)
        cache[key] = scores
        return scores

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        agg = params.get("pair_aggregation", "mean")
        lof = self._target_scores(ctx, params)

        # additive_response: sum over target genes of each gene's mean training delta
        cache = ctx.cache
        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            add = d.mean(axis=0)  # (n_genes,)

            tgenes = ctx.target_genes(p)
            tvals = [lof[g] for g in tgenes if g in lof]
            if len(tvals) == 0:
                score = 0.0
            elif len(tvals) == 1:
                score = float(tvals[0])
            else:
                if agg == "min":
                    score = float(np.min(tvals))
                elif agg == "max":
                    score = float(np.max(tvals))
                else:
                    score = float(np.mean(tvals))

            out[i, :, 0] = add * score

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
