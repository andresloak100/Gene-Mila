import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoeufVarianceTimesAdditiveE651(Feature):
    name = "target_loeuf_variance_times_additive_e651"
    version = 1
    description = "Variance of gnomAD LOEUF across p's target genes, multiplied by additive_response."
    rationale = "Heterogeneous essentiality among targets may modulate the additive response magnitude."
    inputs = ["control_cells", "train_delta", "knowledge"]
    params = {}
    dim = 1

    def _loeuf_map(self, ctx):
        cache = ctx.cache
        key = "_loeuf_map_e651"
        if key in cache:
            return cache[key]
        loeuf = {}
        try:
            k = ctx.knowledge("gene_constraint")
        except Exception:
            k = None
        if k:
            genes = k.get("genes", {})
            cols = k.get("columns", [])
            try:
                idx = cols.index("oe_lof_upper")
            except ValueError:
                idx = None
            if idx is not None:
                for g, vals in genes.items():
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
                        loeuf[g] = fv
        cache[key] = loeuf
        return loeuf

    def compute(self, ctx, perts, params):
        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1))
        loeuf = self._loeuf_map(ctx)

        # additive_response via composition
        try:
            add = ctx.feature("additive_response", perts, None)
            add = np.asarray(add, dtype=float)
            if add.ndim == 3:
                add = add.reshape(add.shape[0], -1)
            elif add.ndim == 1:
                add = add.reshape(-1, 1)
        except Exception:
            add = None

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            vals = []
            for g in tgenes:
                v = loeuf.get(g)
                if v is not None:
                    vals.append(v)
            if len(vals) >= 2:
                var = float(np.var(np.asarray(vals, dtype=float)))
            else:
                var = 0.0

            if add is not None:
                a = add[i]
                if a.size == 1:
                    out[i, :, 0] = a.reshape(()) * var
                else:
                    out[i, :, 0] = a * var
            else:
                _, d = ctx.train_delta(exclude=p)
                out[i, :, 0] = d.mean(axis=0) * var

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
