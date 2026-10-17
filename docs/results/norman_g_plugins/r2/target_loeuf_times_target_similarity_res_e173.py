import numpy as np
from genemila.features.api import Feature, register

@register
class TargetLoeufTimesTargetSimilarityRes(Feature):
    name = "target_loeuf_times_target_similarity_res_e173"
    version = 1
    description = ("Product of the mean target-gene LOEUF (gnomAD LoF constraint) and "
                   "target_similarity_response.")
    rationale = ("LOEUF indicates target importance; the similarity-based transfer already "
                 "borrows signal from similar perturbations, and weighting it by constraint "
                 "may sharpen predictions for constrained targets.")
    inputs = ["knowledge", "feature"]
    params = {}
    dim = 1

    def _loeuf_map(self, ctx):
        cache = ctx.cache
        key = "_e173_loeuf_map"
        if key in cache:
            return cache[key]
        m = {}
        k = ctx.knowledge("gene_constraint")
        if k is not None:
            genes = k.get("genes", {})
            cols = k.get("columns", [])
            try:
                idx = cols.index("oe_lof_upper")
            except ValueError:
                idx = None
            if idx is not None:
                for g, vals in genes.items():
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
                    if np.isfinite(v):
                        m[g] = v
        cache[key] = m
        return m

    def compute(self, ctx, perts, params):
        loeuf = self._loeuf_map(ctx)
        base = ctx.feature("target_similarity_response_e15", perts)
        base = np.asarray(base, dtype=float)
        if base.ndim == 2:
            base = base[:, :, None]
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            vals = [loeuf[g] for g in tg if g in loeuf]
            if vals:
                mean_loeuf = float(np.mean(vals))
            else:
                mean_loeuf = 0.0
            out[i, :, 0] = mean_loeuf * base[i, :, 0]

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
