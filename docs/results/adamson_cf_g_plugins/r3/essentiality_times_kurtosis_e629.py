import numpy as np
from genemila.features.api import Feature, register

@register
class EssentialityTimesKurtosis(Feature):
    name = "essentiality_times_kurtosis_e629"
    version = 1
    description = ("Product of target_essentiality_score_e284 (per perturbation, broadcast over genes) "
                   "and gene_response_kurtosis_e154 (per gene, broadcast over perturbations).")
    rationale = ("Essentiality may modulate the distribution of responses; kurtosis measures tailedness. "
                 "Their interaction could be predictive.")
    inputs = ["knowledge", "train_delta"]
    params = {}
    dim = 1

    def _essentiality(self, ctx):
        cached = ctx.cache.get("_e629_essentiality")
        if cached is not None:
            return cached
        ess = np.zeros(ctx.n_genes, dtype=float)
        kn = ctx.knowledge("gene_constraint")
        if kn is not None:
            genes = kn.get("genes", {}) or {}
            cols = kn.get("columns", []) or []
            # find LOEUF-like column index
            idx = None
            for j, c in enumerate(cols):
                if "oe_lof_upper" in c:
                    idx = j
                    break
            if idx is not None:
                for g, vals in genes.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None or not isinstance(vals, (list, tuple)) or len(vals) <= idx:
                        continue
                    v = vals[idx]
                    if v is None:
                        continue
                    try:
                        v = float(v)
                    except (TypeError, ValueError):
                        continue
                    if not np.isfinite(v):
                        continue
                    # low LOEUF = essential -> map to nonnegative score
                    ess[gi] = max(0.0, 1.0 - v)
        ctx.cache["_e629_essentiality"] = ess
        return ess

    def _kurtosis(self, ctx, p):
        key = ("_e629_kurt", p)
        cached = ctx.cache.get(key)
        if cached is not None:
            return cached
        _, d = ctx.train_delta(exclude=p)
        n = d.shape[0]
        if n < 4:
            kurt = np.zeros(ctx.n_genes, dtype=float)
        else:
            mu = d.mean(axis=0)
            dev = d - mu
            m2 = np.mean(dev * dev, axis=0)
            m4 = np.mean(dev ** 4, axis=0)
            with np.errstate(divide="ignore", invalid="ignore"):
                kurt = np.where(m2 > 0, m4 / (m2 * m2) - 3.0, 0.0)
            kurt = np.nan_to_num(kurt, nan=0.0, posinf=0.0, neginf=0.0)
        ctx.cache[key] = kurt
        return kurt

    def compute(self, ctx, perts, params):
        ess = self._essentiality(ctx)
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            tgt = ctx.target_indices(p)
            if tgt:
                s = float(np.mean(ess[tgt]))
            else:
                s = 0.0
            kurt = self._kurtosis(ctx, p)
            out[i, :, 0] = s * kurt
        return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
