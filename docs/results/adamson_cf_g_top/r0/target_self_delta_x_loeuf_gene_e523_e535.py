import numpy as np
from genemila.features.api import Feature, register


@register
class TargetSelfDeltaXLoeufGene_e523_e535(Feature):
    name = "target_self_delta_x_loeuf_gene_e523_e535"
    version = 1
    description = (
        "For each (p,g): standardized target_self_delta_e54 * standardized (1 - LOEUF_gene)."
    )
    rationale = (
        "The effect of a perturbation on its own target may be more predictive for genes "
        "that are essential (low LOEUF); the interaction captures whether target-self effects "
        "propagate preferentially through essential gene products."
    )
    inputs = ["knowledge", "feature"]
    params = {}
    dim = 1

    def _loeuf_vec(self, ctx):
        key = "_loeuf_ess_std"
        cache = ctx.cache
        if key in cache:
            return cache[key]
        G = ctx.n_genes
        loeuf = np.full(G, np.nan, dtype=float)
        ann = ctx.knowledge("gene_constraint")
        if ann is not None:
            genes_map = ann.get("genes", {})
            cols = ann.get("columns", [])
            try:
                oe_idx = cols.index("oe_lof_upper")
            except ValueError:
                oe_idx = None
            if oe_idx is not None:
                for gi, gname in enumerate(ctx.genes):
                    vals = genes_map.get(gname)
                    if vals is None:
                        continue
                    try:
                        v = vals[oe_idx]
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

        essential = 1.0 - loeuf
        valid = np.isfinite(essential)
        ess_std = np.zeros(G, dtype=float)
        if valid.sum() > 1:
            mu = essential[valid].mean()
            sd = essential[valid].std()
            if not np.isfinite(sd) or sd == 0:
                sd = 1.0
            ess_std[valid] = (essential[valid] - mu) / sd
        cache[key] = ess_std
        return ess_std

    def compute(self, ctx, perts, params):
        n = len(perts)
        G = ctx.n_genes
        out = np.zeros((n, G, 1), dtype=float)

        ess_std = self._loeuf_vec(ctx)

        # target_self_delta_e54 for each (p, g)
        tsd = None
        try:
            tsd = ctx.feature("target_self_delta_e54", perts, params=None)
            tsd = np.asarray(tsd, dtype=float)
            if tsd.ndim == 3:
                tsd = tsd[:, :, 0]
            elif tsd.ndim != 2:
                tsd = None
        except Exception:
            tsd = None

        if tsd is None:
            # Fallback: compute target-self delta directly from training data.
            tsd = np.zeros((n, G), dtype=float)
            for i, p in enumerate(perts):
                idx = ctx.target_indices(p)
                if not idx:
                    continue
                try:
                    _, deltas = ctx.train_delta(exclude=p)
                except Exception:
                    continue
                deltas = np.asarray(deltas, dtype=float)
                if deltas.size == 0:
                    continue
                mean_d = deltas.mean(axis=0)
                tsd[i, idx] = mean_d[idx]
        else:
            if tsd.shape != (n, G):
                fixed = np.zeros((n, G), dtype=float)
                r = min(tsd.shape[0], n)
                c = min(tsd.shape[1], G)
                fixed[:r, :c] = tsd[:r, :c]
                tsd = fixed

        tsd = np.where(np.isfinite(tsd), tsd, 0.0)

        # Standardize target_self_delta per row (across genes)
        row_mean = tsd.mean(axis=1, keepdims=True)
        row_std = tsd.std(axis=1, keepdims=True)
        row_std = np.where((row_std > 0) & np.isfinite(row_std), row_std, 1.0)
        tsd_std = (tsd - row_mean) / row_std

        out[:, :, 0] = tsd_std * ess_std[None, :]
        out = np.where(np.isfinite(out), out, 0.0)
        return out
