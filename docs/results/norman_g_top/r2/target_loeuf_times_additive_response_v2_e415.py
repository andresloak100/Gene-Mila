import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoeufTimesAdditiveResponseV2E415(Feature):
    name = "target_loeuf_times_additive_response_v2_e415"
    version = 1
    description = ("Product of the mean normalized LOEUF (z-scored across all genes) of p's "
                   "target genes and the additive_response prediction.")
    rationale = ("Loss-of-function intolerant genes may have stronger regulatory roles; "
                 "z-scoring LOEUF removes scale issues so the interaction with the additive "
                 "baseline is comparable across genes.")
    inputs = ["control_cells", "knowledge"]
    params = {}
    dim = 1

    def _loeuf_vector(self, ctx):
        cache = ctx.cache
        key = "_loeuf_z_e415"
        if key in cache:
            return cache[key]
        n = ctx.n_genes
        loeuf = np.full(n, np.nan, dtype=float)
        k = ctx.knowledge("gene_constraint")
        if k is not None:
            cols = k.get("columns", [])
            genes = k.get("genes", {})
            if "oe_lof_upper" in cols:
                j = cols.index("oe_lof_upper")
                for i, g in enumerate(ctx.genes):
                    vals = genes.get(g)
                    if vals is None:
                        continue
                    try:
                        v = vals[j]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        loeuf[i] = fv
        # z-score across genes with finite LOEUF
        z = np.zeros(n, dtype=float)
        mask = np.isfinite(loeuf)
        if mask.sum() >= 2:
            mu = loeuf[mask].mean()
            sd = loeuf[mask].std()
            if sd > 0:
                z[mask] = (loeuf[mask] - mu) / sd
        cache[key] = z
        return z

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1), dtype=float)
        loeuf_z = self._loeuf_vector(ctx)

        # additive_response feature (composition)
        try:
            add = ctx.feature("additive_response", perts)
        except Exception:
            add = None

        for i, p in enumerate(perts):
            tidx = ctx.target_indices(p)
            if len(tidx) == 0:
                scale = 0.0
            else:
                scale = float(loeuf_z[tidx].mean())

            if add is not None:
                base = np.asarray(add[i]).reshape(-1)
                if base.shape[0] != n:
                    base = np.zeros(n, dtype=float)
            else:
                base = np.zeros(n, dtype=float)

            out[i, :, 0] = scale * base

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
