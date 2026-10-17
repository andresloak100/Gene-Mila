import numpy as np
from genemila.features.api import Feature, register


@register
class ConstraintWeightedTargetMeanSimilarityE332(Feature):
    name = "constraint_weighted_target_mean_similari_e332"
    version = 1
    description = (
        "target_response_similarity_to_mean_e110 weighted by the mean LoF "
        "constraint (inverse LOEUF or pLI) of the perturbation's target genes."
    )
    rationale = (
        "LoF-intolerant target genes (low LOEUF / high pLI) are more likely to "
        "have strong downstream effects when activated, so weighting the target "
        "mean-response similarity by constraint may sharpen the signal."
    )
    inputs = ["target_response_similarity_to_mean_e110", "knowledge:gene_constraint"]
    params = {"constraint_metric": "inverse_loeuf"}
    dim = 1

    def _build_constraint_map(self, ctx, metric):
        """Return dict gene -> constraint weight, plus median fallback."""
        kc = ctx.knowledge("gene_constraint")
        weights = {}
        if kc is not None:
            genes = kc.get("genes", {}) or {}
            columns = kc.get("columns", []) or []
            # locate relevant column indices
            try:
                if metric == "pli":
                    idx = columns.index("pLI")
                else:
                    idx = columns.index("oe_lof_upper")
            except ValueError:
                idx = None
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
                    if not np.isfinite(fv):
                        continue
                    if metric == "pli":
                        w = fv
                    else:
                        # inverse LOEUF; guard against zero
                        w = 1.0 / fv if fv > 0 else np.nan
                    if np.isfinite(w):
                        weights[g] = w
        # median fallback from observed weights
        if len(weights) > 0:
            med = float(np.median(np.array(list(weights.values()), dtype=float)))
        else:
            med = 1.0
        return weights, med

    def compute(self, ctx, perts, params):
        metric = params.get("constraint_metric", "inverse_loeuf")
        if metric not in ("inverse_loeuf", "pli"):
            metric = "inverse_loeuf"

        cache = ctx.cache
        key = ("constraint_map_e332", metric)
        if key in cache:
            weights, med = cache[key]
        else:
            weights, med = self._build_constraint_map(ctx, metric)
            cache[key] = (weights, med)

        # base feature values: (n_perts, n_genes, dim)
        base = ctx.feature(
            "target_response_similarity_to_mean_e110", perts, params=None
        )
        base = np.asarray(base, dtype=float)
        if base.ndim == 2:
            base = base[:, :, None]
        base = np.where(np.isfinite(base), base, 0.0)

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if targets:
                vals = [weights.get(g, med) for g in targets]
                w = float(np.mean(vals))
            else:
                w = med
            if not np.isfinite(w):
                w = med
            out[i, :, 0] = base[i, :, 0] * w

        out = np.where(np.isfinite(out), out, 0.0)
        return out
