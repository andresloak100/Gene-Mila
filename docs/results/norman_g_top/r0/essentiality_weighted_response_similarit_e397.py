import numpy as np
from genemila.features.api import Feature, register


@register
class EssentialityWeightedResponseSimilarity(Feature):
    name = "essentiality_weighted_response_similarit_e397"
    version = 1
    description = ("Leave-one-out weighted average of training perturbation deltas, "
                   "weighted by target-gene similarity times an essentiality score "
                   "derived from LOEUF constraint.")
    rationale = ("Loss-of-function intolerant genes may produce stronger/more consistent "
                 "transcriptional responses when perturbed; weighting the similarity-based "
                 "neighbour average by target essentiality refines the prediction.")
    inputs = ["train_delta", "gene_corr", "knowledge"]
    params = {"essentiality_metric": "loeuf_inverse", "power": 1.0}
    dim = 1

    def _essentiality(self, ctx, params):
        cache = ctx.cache
        key = ("e397_ess", params.get("essentiality_metric", "loeuf_inverse"))
        if key in cache:
            return cache[key]

        n = ctx.n_genes
        ess = np.ones(n, dtype=float)
        metric = params.get("essentiality_metric", "loeuf_inverse")

        kc = None
        for nm in ("gene_constraint",):
            try:
                kc = ctx.knowledge(nm)
            except Exception:
                kc = None
            if kc is not None:
                break

        if kc is not None and isinstance(kc, dict):
            cols = kc.get("columns", [])
            genes = kc.get("genes", {})
            # find LOEUF column
            loeuf_idx = None
            for j, c in enumerate(cols):
                if "oe_lof_upper" in str(c).lower() or "loeuf" in str(c).lower():
                    loeuf_idx = j
                    break
            if loeuf_idx is not None and isinstance(genes, dict):
                loeuf = np.full(n, np.nan, dtype=float)
                for g, vals in genes.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None:
                        continue
                    try:
                        v = vals[loeuf_idx]
                    except Exception:
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except Exception:
                        continue
                    if np.isfinite(fv):
                        loeuf[gi] = fv
                finite = np.isfinite(loeuf)
                if finite.any():
                    med = float(np.median(loeuf[finite]))
                    if not np.isfinite(med) or med <= 0:
                        med = 1.0
                    filled = np.where(finite, loeuf, med)
                    filled = np.clip(filled, 1e-3, None)
                    if metric == "loeuf_inverse":
                        ess = 1.0 / filled
                    else:
                        ess = filled
                    # standardise to mean 1 over measured genes
                    m = ess[finite].mean()
                    if np.isfinite(m) and m > 0:
                        ess = ess / m
        cache[key] = ess
        return ess

    def _target_sim(self, ctx, p, q):
        tp = ctx.target_indices(p)
        tq = ctx.target_indices(q)
        if not tp or not tq:
            return 0.0
        # mean of pairwise correlations between target sets
        vals = []
        for a in tp:
            for b in tq:
                vals.append(ctx.gene_corr[a, b])
        if not vals:
            return 0.0
        s = float(np.mean(vals))
        if not np.isfinite(s):
            return 0.0
        return s

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1), dtype=float)
        ess = self._essentiality(ctx, params)
        power = float(params.get("power", 1.0))

        for i, p in enumerate(perts):
            ids, deltas = ctx.train_delta(exclude=p)
            if len(ids) == 0:
                continue
            weights = np.zeros(len(ids), dtype=float)
            for j, q in enumerate(ids):
                if q == p:
                    continue
                sim = self._target_sim(ctx, p, q)
                if sim == 0.0:
                    continue
                tq = ctx.target_indices(q)
                if tq:
                    e = float(np.mean(ess[tq]))
                else:
                    e = 1.0
                if not np.isfinite(e):
                    e = 1.0
                if e <= 0:
                    e = 1e-6
                weights[j] = sim * (e ** power)

            wsum = weights.sum()
            if not np.isfinite(wsum) or wsum <= 0:
                # fallback: unweighted mean
                out[i, :, 0] = deltas.mean(axis=0)
            else:
                out[i, :, 0] = (weights[:, None] * deltas).sum(axis=0) / wsum

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
