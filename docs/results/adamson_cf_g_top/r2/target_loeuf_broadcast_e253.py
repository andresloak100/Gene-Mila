import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoeufBroadcastE253(Feature):
    name = "target_loeuf_broadcast_e253"
    version = 1
    description = "LOEUF (LoF intolerance) of the perturbation target gene, broadcast to all genes."
    rationale = ("LoF-intolerant targets are often essential; their perturbation may drive stronger "
                 "downstream expression changes. A per-target scalar encodes this intensity globally.")
    inputs = ["knowledge", "target_genes"]
    params = {"metric": "oe_lof_upper"}
    dim = 1

    def compute(self, ctx, perts, params):
        metric = params.get("metric", "oe_lof_upper")
        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1), dtype=float)

        cache = ctx.cache
        if "constraint_map" not in cache:
            constraint = ctx.knowledge("gene_constraint") or {}
            genes = constraint.get("genes", {}) or {}
            cols = constraint.get("columns", []) or []
            try:
                idx = cols.index(metric)
            except ValueError:
                idx = 0
            cmap = {}
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
                    cmap[sym] = fv
            cache["constraint_map"] = cmap
        cmap = cache["constraint_map"]

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            val = 0.0
            for t in targets:
                if t in cmap:
                    val = cmap[t]
                    break
            out[i, :, 0] = val

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
