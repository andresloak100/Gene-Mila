import numpy as np
from genemila.features.api import Feature, register


@register
class LofWeightedPairAdditivityResidual(Feature):
    name = "lof_weighted_pair_additivity_residual_e1_e646"
    version = 1
    description = ("For a pair A+B, weighted average (over training pairs) of the additivity "
                   "residual delta[q,g] - (delta_C + delta_D), weighted by target LoF intolerance.")
    rationale = ("LoF-intolerant (low LOEUF) target genes may show stronger non-additive "
                 "downstream effects, so weighting training pairs by their target constraint "
                 "should sharpen the predicted pair residual.")
    inputs = ["train_delta", "knowledge"]
    params = {"weight_power": 1.0}
    dim = 1

    def _lof(self, ctx):
        cached = ctx.cache.get("_lof_map_e646")
        if cached is not None:
            return cached
        lof = {}
        try:
            k = ctx.knowledge("gene_constraint")
        except Exception:
            k = None
        if isinstance(k, dict):
            genes = k.get("genes", {})
            cols = k.get("columns", [])
            try:
                idx = cols.index("oe_lof_upper")
            except ValueError:
                idx = None
            if idx is not None and isinstance(genes, dict):
                for g, vals in genes.items():
                    if vals is None:
                        continue
                    try:
                        v = vals[idx]
                    except Exception:
                        continue
                    if v is None:
                        continue
                    try:
                        v = float(v)
                    except Exception:
                        continue
                    if np.isfinite(v) and v > 0:
                        lof[g] = v
        ctx.cache["_lof_map_e646"] = lof
        return lof

    def _pair_targets(self, ctx, p):
        try:
            tg = ctx.target_genes(p)
        except Exception:
            tg = []
        return list(tg) if tg else []

    def compute(self, ctx, perts, params):
        weight_power = float(params.get("weight_power", 1.0))
        lof = self._lof(ctx)
        n_genes = ctx.n_genes

        # Precompute per-perturbation target gene names and their constraint weights.
        target_cache = {}
        for p in ctx.perts:
            target_cache[p] = self._pair_targets(ctx, p)

        def pert_weight(p):
            tg = target_cache.get(p, [])
            if len(tg) < 2:
                return None
            w = 0.0
            for g in tg:
                v = lof.get(g)
                if v is None or not np.isfinite(v) or v <= 0:
                    return None
                w += (1.0 / v) ** weight_power
            return w

        # Precompute single-gene deltas keyed by gene name (perturbation id == gene for singles).
        out = np.zeros((len(perts), n_genes, 1))

        for i, p in enumerate(perts):
            tg = target_cache.get(p, [])
            if len(tg) < 2:
                continue  # single-gene perturbation -> 0

            _, deltas = ctx.train_delta(exclude=p)
            train_ids = None
            # train_delta returns (pert_ids, array); recompute to get ids
            try:
                train_ids, deltas = ctx.train_delta(exclude=p)
            except Exception:
                continue
            if train_ids is None:
                continue

            # Build lookup of single-gene deltas within the training set (excluding p).
            single_delta = {}
            for j, q in enumerate(train_ids):
                q_tg = target_cache.get(q, [])
                if len(q_tg) == 1:
                    single_delta[q_tg[0]] = deltas[j]

            num = np.zeros(n_genes, dtype=np.float64)
            den = 0.0

            for j, q in enumerate(train_ids):
                q_tg = target_cache.get(q, [])
                if len(q_tg) < 2:
                    continue
                w = pert_weight(q)
                if w is None:
                    continue
                # additive baseline using single deltas of the pair's targets
                base = np.zeros(n_genes, dtype=np.float64)
                ok = True
                for g in q_tg:
                    d = single_delta.get(g)
                    if d is None:
                        ok = False
                        break
                    base += d
                if not ok:
                    continue
                residual = deltas[j] - base
                num += w * residual
                den += w

            if den > 0:
                out[i, :, 0] = num / den

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
