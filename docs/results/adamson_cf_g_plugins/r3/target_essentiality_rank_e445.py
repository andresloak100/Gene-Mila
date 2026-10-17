import numpy as np
from genemila.features.api import Feature, register


@register
class TargetEssentialityRankE445(Feature):
    name = "target_essentiality_rank_e445"
    version = 1
    description = "Rank of target gene's LOEUF among all genes with LOEUF values, scaled to [0,1]."
    rationale = ("Essential genes may have stronger downstream effects when perturbed; "
                 "rank normalization captures relative intolerance across genes.")
    inputs = ["knowledge", "target_genes"]
    params = {}
    dim = 1

    def _build_rank_table(self, ctx):
        cache = ctx.cache
        key = "__loeuf_rank_table_e445__"
        if key in cache:
            return cache[key]

        # Collect LOEUF values (oe_lof_upper) for all genes in the constraint table.
        loeuf = {}
        try:
            kc = ctx.knowledge("gene_constraint")
        except Exception:
            kc = None

        if kc is not None:
            genes = kc.get("genes", {}) or {}
            cols = kc.get("columns", []) or []
            # Find index of oe_lof_upper column
            idx = None
            for i, c in enumerate(cols):
                if isinstance(c, str) and c.lower() == "oe_lof_upper":
                    idx = i
                    break
            if idx is not None:
                for sym, vals in genes.items():
                    if not isinstance(vals, (list, tuple)) or len(vals) <= idx:
                        continue
                    v = vals[idx]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if not np.isfinite(fv):
                        continue
                    loeuf[sym] = fv

        # Build sorted array of LOEUF values for ranking.
        if len(loeuf) == 0:
            cache[key] = (None, None)
            return cache[key]

        symbols = list(loeuf.keys())
        vals = np.array([loeuf[s] for s in symbols], dtype=float)
        order = np.argsort(vals, kind="mergesort")
        sorted_vals = vals[order]
        n = len(sorted_vals)

        # Precompute rank (percentile) for each gene: lower LOEUF -> higher essentiality.
        # We want rank scaled to [0,1] where low LOEUF -> high value.
        # Use average rank for ties via searchsorted on sorted values.
        # rank position (0-based) of value; use left/right for tie averaging.
        result = {}
        left = np.searchsorted(sorted_vals, vals, side="left")
        right = np.searchsorted(sorted_vals, vals, side="right")
        avg_rank = (left + right - 1) / 2.0  # 0-based average rank
        if n > 1:
            scaled = 1.0 - avg_rank / (n - 1)
        else:
            scaled = np.ones_like(avg_rank)
        for s, v in zip(symbols, scaled):
            result[s] = float(v)

        cache[key] = (result, n)
        return cache[key]

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        table, n = self._build_rank_table(ctx)

        if table is None:
            return out

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            val = 0.0
            if tg:
                # Use first target gene that has a LOEUF value.
                for g in tg:
                    if g in table:
                        val = table[g]
                        break
            out[i, :, 0] = val

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
