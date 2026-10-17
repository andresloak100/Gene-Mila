import numpy as np
from genemila.features.api import Feature, register


@register
class LoefWeightedTargetResponseSimilarity(Feature):
    name = "loef_weighted_target_response_similarity_e287"
    version = 1
    description = ("For perturbation p and gene g, weighted average (inverse LOEUF) of the "
                   "max Pearson correlation between g's response vector and each target's "
                   "single-gene response vector.")
    rationale = ("Loss-of-function intolerant target genes are more likely to have strong, "
                 "specific transcriptional responses, so their response vectors should be "
                 "more informative when weighting target similarity.")
    inputs = ["train_delta", "knowledge:gene_constraint"]
    params = {"weight_power": 1.0}
    dim = 1

    def _get_loef(self, ctx):
        cache = ctx.cache
        key = "_e287_loef"
        if key in cache:
            return cache[key]
        loef = np.full(ctx.n_genes, np.nan, dtype=float)
        try:
            data = ctx.knowledge("gene_constraint")
        except Exception:
            data = None
        if data is not None:
            genes = data.get("genes", {}) or {}
            cols = data.get("columns", []) or []
            try:
                idx = list(cols).index("oe_lof_upper")
            except ValueError:
                idx = None
            if idx is not None:
                for i, g in enumerate(ctx.genes):
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
                        loef[i] = fv
        cache[key] = loef
        return loef

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        n_perts = len(perts)
        out = np.zeros((n_perts, n_genes, 1), dtype=float)

        loef = self._get_loef(ctx)
        power = float(params.get("weight_power", 1.0))

        # Precompute per-perturbation leave-one-out delta matrices and correlations lazily.
        # For each perturbation p, we need:
        #   - delta matrix D (training perts x genes) excluding p
        #   - correlation of each gene g with each target gene t across training perturbations
        #     i.e. corr over rows of D[:, g] vs D[:, t].
        # We compute corr(D[:, g], D[:, t]) for all g and a small set of target columns t.

        for i, p in enumerate(perts):
            targets = ctx.target_indices(p)
            if not targets:
                continue

            # Weights from inverse LOEUF
            weights = np.zeros(len(targets), dtype=float)
            for j, t in enumerate(targets):
                lv = loef[t]
                if np.isfinite(lv) and lv > 0:
                    weights[j] = (1.0 / lv) ** power
                else:
                    weights[j] = 0.0
            wsum = weights.sum()
            if wsum <= 0:
                continue
            weights = weights / wsum

            _, D = ctx.train_delta(exclude=p)
            D = np.asarray(D, dtype=float)
            if D.ndim != 2 or D.shape[0] < 2:
                continue

            # Center once
            Dc = D - D.mean(axis=0, keepdims=True)
            # norms per gene
            norms = np.sqrt(np.sum(Dc * Dc, axis=0))
            # avoid division by zero
            safe_norms = np.where(norms > 0, norms, 1.0)

            # For each target t, compute correlation of every gene g with t
            # corr_g_t = sum_g_t / (norm_g * norm_t)
            # Dc[:, t] column
            weighted_corr = np.zeros(n_genes, dtype=float)
            for j, t in enumerate(targets):
                w = weights[j]
                if w == 0.0:
                    continue
                col_t = Dc[:, t]
                norm_t = safe_norms[t]
                if norm_t <= 0:
                    continue
                # numerator for all g
                num = Dc.T @ col_t  # shape (n_genes,)
                denom = safe_norms * norm_t
                corr = num / denom
                # clamp
                corr = np.clip(corr, -1.0, 1.0)
                weighted_corr += w * corr

            out[i, :, 0] = weighted_corr

        # Ensure finite
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
