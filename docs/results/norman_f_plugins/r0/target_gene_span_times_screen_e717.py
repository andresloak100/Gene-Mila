import numpy as np
from genemila.features.api import Feature, register


def _to_float(v):
    """Best-effort scalar extraction from a possibly nested/list value."""
    if v is None:
        return None
    if isinstance(v, (int, float, np.integer, np.floating)):
        f = float(v)
        return f if np.isfinite(f) else None
    if isinstance(v, (list, tuple, np.ndarray)):
        vals = []
        for x in np.asarray(v).ravel().tolist():
            try:
                fx = float(x)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fx):
                vals.append(fx)
        if not vals:
            return None
        return float(np.mean(vals))
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return f if np.isfinite(f) else None


@register
class TargetGeneSpanTimesScreenE717(Feature):
    name = "target_gene_span_times_screen_e717"
    version = 1
    description = (
        "Sum of gene_span_kb over perturbation targets multiplied by the signed "
        "Replogle screen delta."
    )
    rationale = (
        "Gene span is a proxy for chromatin domain size; larger targets may have broader "
        "effects. Multiplying the total target span by the external signed screen delta "
        "modulates the external evidence by target size."
    )
    inputs = ["gene_annotation", "replogle2022_k562"]
    params = {}
    dim = 1

    def _span_map(self, ctx):
        key = "_span_map_e717"
        if key in ctx.cache:
            return ctx.cache[key]
        span_map = {}
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes_ann = ann.get("genes", {}) or {}
            cols = ann.get("columns", []) or []
            span_idx = 0
            if "gene_span_kb" in cols:
                span_idx = cols.index("gene_span_kb")
            for g, vals in genes_ann.items():
                if vals is None:
                    continue
                if isinstance(vals, dict):
                    v = vals.get("gene_span_kb")
                else:
                    try:
                        v = vals[span_idx]
                    except (IndexError, KeyError, TypeError):
                        continue
                f = _to_float(v)
                if f is not None:
                    span_map[g] = f
        ctx.cache[key] = span_map
        return span_map

    def _screen_map(self, ctx):
        key = "_screen_map_e717"
        if key in ctx.cache:
            return ctx.cache[key]
        sign = -1.0
        repl_perts = {}
        repl = ctx.knowledge("replogle2022_k562")
        if repl is not None:
            s = _to_float(repl.get("sign"))
            if s is not None:
                sign = s
            repl_perts = repl.get("perts", {}) or {}
        screen_map = {}
        for g, entry in repl_perts.items():
            if isinstance(entry, dict):
                d = _to_float(entry.get("delta"))
            else:
                d = _to_float(entry)
            if d is None:
                continue
            screen_map[g] = sign * d
        res = (sign, screen_map)
        ctx.cache[key] = res
        return res

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        span_map = self._span_map(ctx)
        _, screen_map = self._screen_map(ctx)

        out = np.zeros((len(perts), n, 1), dtype=np.float64)

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p) or []
            span_sum = 0.0
            screen_sum = 0.0
            for g in targets:
                span_sum += span_map.get(g, 0.0)
                screen_sum += screen_map.get(g, 0.0)
            out[i, :, 0] = span_sum * screen_sum

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
