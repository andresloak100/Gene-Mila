import numpy as np
from genemila.features.api import Feature, register


@register
class IsTargetXLoeufGeneE37(Feature):
    name = "is_target_x_loeuf_gene_e37"
    version = 1
    description = "Interaction of is_target with the target gene's LOEUF constraint score."
    rationale = (
        "Direct knockdown of an LoF-intolerant gene (low LOEUF) may produce a larger "
        "self-expression change than knockdown of a tolerant gene; the interaction "
        "captures this target-specific, constraint-dependent effect."
    )
    inputs = ["gene_constraint", "target_indices"]
    params = {"fill_missing": "median"}
    dim = 1

    def _loeuf_vector(self, ctx, fill_missing):
        cache = ctx.cache
        key = "_e37_loeuf_vector"
        if key in cache:
            return cache[key]

        loeuf = np.full(ctx.n_genes, np.nan, dtype=float)
        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            genes_tbl = kc.get("genes", {}) or {}
            cols = kc.get("columns", []) or []
            try:
                loeuf_col = cols.index("oe_lof_upper")
            except ValueError:
                loeuf_col = None
            if loeuf_col is not None:
                for g, vals in genes_tbl.items():
                    idx = ctx.gene_index.get(g)
                    if idx is None or vals is None:
                        continue
                    if loeuf_col >= len(vals):
                        continue
                    v = vals[loeuf_col]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        loeuf[idx] = fv

        finite = np.isfinite(loeuf)
        if finite.any():
            if fill_missing == "median":
                fill_val = float(np.median(loeuf[finite]))
            elif fill_missing == "mean":
                fill_val = float(np.mean(loeuf[finite]))
            elif fill_missing == "zero":
                fill_val = 0.0
            else:
                fill_val = float(np.median(loeuf[finite]))
        else:
            fill_val = 0.0

        loeuf[~finite] = fill_val
        cache[key] = loeuf
        return loeuf

    def compute(self, ctx, perts, params):
        fill_missing = params.get("fill_missing", "median")
        loeuf = self._loeuf_vector(ctx, fill_missing)

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            idxs = ctx.target_indices(p)
            if not idxs:
                continue
            idxs = np.asarray(idxs, dtype=int)
            idxs = idxs[(idxs >= 0) & (idxs < ctx.n_genes)]
            if idxs.size:
                out[i, idxs, 0] = loeuf[idxs]

        out[~np.isfinite(out)] = 0.0
        return out
