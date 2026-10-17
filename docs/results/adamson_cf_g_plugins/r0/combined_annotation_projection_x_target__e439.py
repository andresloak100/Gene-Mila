import numpy as np
from genemila.features.api import Feature, register


@register
class CombinedAnnotationProjectionXTargetE439(Feature):
    name = "combined_annotation_projection_x_target__e439"
    version = 1
    description = (
        "Interaction of combined annotation projection (e398) with target essentiality "
        "(1 - LOEUF_target)."
    )
    rationale = (
        "The combined annotation projection captures functional similarity; essential "
        "targets may amplify this effect, so an interaction term may capture synergy."
    )
    inputs = ["knowledge", "feature"]
    params = {}
    dim = 1

    def _loeuf_map(self, ctx):
        key = "_e439_loeuf_map"
        cached = ctx.cache.get(key)
        if cached is not None:
            return cached
        loeuf = {}
        kn = ctx.knowledge("gene_constraint")
        if kn is not None:
            genes = kn.get("genes", {}) or {}
            cols = kn.get("columns", []) or []
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
                    if np.isfinite(fv):
                        loeuf[sym] = fv
        ctx.cache[key] = loeuf
        return loeuf

    def compute(self, ctx, perts, params):
        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1), dtype=float)
        if n == 0:
            return out

        proj = ctx.feature(
            "combined_annotation_projection_target_in_e398", perts, params=None
        )
        proj = np.asarray(proj, dtype=float)
        if proj.ndim == 3:
            proj = proj[:, :, 0]
        elif proj.ndim == 1:
            proj = proj.reshape(n, ctx.n_genes)

        loeuf = self._loeuf_map(ctx)

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            val = None
            for t in targets:
                if t in loeuf:
                    val = loeuf[t]
                    break
            if val is None:
                # fall back to first target gene even if unconstrained
                factor = 1.0
            else:
                factor = 1.0 - val
            out[i, :, 0] = proj[i] * factor

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
