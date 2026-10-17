import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoeufXGeneSpecificity(Feature):
    name = "target_loeuf_x_gene_specificity_e291_e301"
    version = 1
    description = ("Product of inverted target LOEUF (from gnomAD oe_lof_upper) and "
                   "per-gene expression specificity (tau-like) across control cells.")
    rationale = ("LoF-intolerant (low LOEUF) targets are likely essential; their knockdown "
                 "may preferentially affect genes with high expression specificity. The "
                 "interaction of target constraint and gene specificity captures this.")
    inputs = ["control_cells", "gene_constraint"]
    params = {"specificity_metric": "tau", "loeuf_default": 1.0}
    dim = 1

    def _specificity(self, ctx, params):
        key = ("spec", params.get("specificity_metric", "tau"))
        cache = ctx.cache
        if key in cache:
            return cache[key]

        X = np.asarray(ctx.control_cells, dtype=np.float64)
        # Per-gene mean expression across control cells
        mean_expr = X.mean(axis=0)  # (n_genes,)
        metric = params.get("specificity_metric", "tau")

        if metric == "tau":
            # Tau statistic: sum(1 - x_i/max) / (n - 1), x_i clipped to >= 0
            Xc = np.clip(X, 0.0, None)
            maxv = Xc.max(axis=0)
            n = Xc.shape[0]
            safe_max = np.where(maxv > 0, maxv, 1.0)
            ratio = Xc / safe_max[None, :]
            tau = (1.0 - ratio).sum(axis=0) / max(n - 1, 1)
            spec = np.clip(tau, 0.0, 1.0)
        else:
            # Inverse breadth: 1 - mean/max
            maxv = np.clip(X, 0.0, None).max(axis=0)
            safe_max = np.where(maxv > 0, maxv, 1.0)
            spec = 1.0 - (np.clip(mean_expr, 0.0, None) / safe_max)
            spec = np.clip(spec, 0.0, 1.0)

        spec = np.where(np.isfinite(spec), spec, 0.0)
        cache[key] = spec
        return spec

    def _loeuf_map(self, ctx, default):
        key = ("loeuf_map",)
        cache = ctx.cache
        if key in cache:
            return cache[key]

        loeuf = {}
        gc = ctx.knowledge("gene_constraint")
        if gc is not None:
            cols = gc.get("columns", [])
            genes = gc.get("genes", {}) or {}
            try:
                idx = cols.index("oe_lof_upper")
            except ValueError:
                idx = None
            if idx is not None:
                for sym, vals in genes.items():
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
                    if np.isfinite(fv) and fv > 0:
                        loeuf[sym] = fv
        cache[key] = (loeuf, default)
        return cache[key]

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        n_genes = ctx.n_genes
        out = np.zeros((n_perts, n_genes, 1), dtype=np.float64)

        spec = self._specificity(ctx, params)
        default = float(params.get("loeuf_default", 1.0))
        loeuf_map, _ = self._loeuf_map(ctx, default)

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            loeuf_vals = []
            for g in tg:
                if g in loeuf_map:
                    loeuf_vals.append(loeuf_map[g])
            if loeuf_vals:
                loeuf = float(np.mean(loeuf_vals))
            else:
                loeuf = default
            if not np.isfinite(loeuf) or loeuf <= 0:
                loeuf = default
            inv_loeuf = 1.0 / loeuf
            out[i, :, 0] = inv_loeuf * spec

        out = np.where(np.isfinite(out), out, 0.0)
        return out
