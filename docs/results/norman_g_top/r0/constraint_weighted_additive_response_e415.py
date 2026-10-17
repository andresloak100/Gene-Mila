import numpy as np
from genemila.features.api import Feature, register


@register
class ConstraintWeightedAdditiveResponseE415(Feature):
    name = "constraint_weighted_additive_response_e415"
    version = 1
    description = ("Additive response scaled by the average LoF-intolerance "
                   "(1 - LOEUF or pLI) of the perturbation's target genes.")
    rationale = ("Perturbations of constrained/essential genes may produce larger or "
                 "more consistent downstream effects; constraint is independent of "
                 "expression data and can modulate the additive response.")
    inputs = ["knowledge", "feature", "target_genes"]
    params = {"constraint_metric": "loeuf"}
    dim = 1

    def _target_weight(self, ctx, p, metric, cache):
        genes = ctx.target_genes(p)
        if not genes:
            return 0.0
        gc = cache.get("gc")
        if gc is None:
            gc = ctx.knowledge("gene_constraint") or {}
            cache["gc"] = gc
        table = gc.get("genes", {}) if isinstance(gc, dict) else {}
        cols = gc.get("columns", []) if isinstance(gc, dict) else []
        if metric == "pli":
            key = "pLI"
            if key not in cols:
                for c in cols:
                    if c.lower() == "pli":
                        key = c
                        break
            idx = cols.index(key) if key in cols else None
        else:
            key = "oe_lof_upper"
            if key not in cols:
                for c in cols:
                    if c.lower() in ("oe_lof_upper", "loeuf"):
                        key = c
                        break
            idx = cols.index(key) if key in cols else None

        vals = []
        for g in genes:
            row = table.get(g)
            if row is None or idx is None:
                continue
            v = row[idx]
            if v is None:
                continue
            try:
                v = float(v)
            except (TypeError, ValueError):
                continue
            if not np.isfinite(v):
                continue
            if metric == "pli":
                w = v  # pLI already in [0,1], higher = more constrained
            else:
                w = 1.0 - v  # low LOEUF = constrained -> weight near 1
            vals.append(w)
        if not vals:
            return 0.0
        return float(np.mean(vals))

    def compute(self, ctx, perts, params):
        metric = str(params.get("constraint_metric", "loeuf")).lower()
        if metric not in ("loeuf", "pli"):
            metric = "loeuf"
        cache = ctx.cache
        base = ctx.feature("additive_response", perts)
        base = np.asarray(base, dtype=float)
        if base.ndim == 3:
            base = base[:, :, 0]
        out = np.zeros((len(perts), ctx.n_genes, 1))
        for i, p in enumerate(perts):
            w = self._target_weight(ctx, p, metric, cache)
            out[i, :, 0] = base[i] * w
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
