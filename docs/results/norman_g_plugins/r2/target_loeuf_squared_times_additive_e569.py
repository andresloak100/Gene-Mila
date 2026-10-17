import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoeufSquaredTimesAdditive(Feature):
    name = "target_loeuf_squared_times_additive_e569"
    version = 1
    description = (
        "Square the mean LOEUF of p's target genes, then multiply by additive_response."
    )
    rationale = (
        "Captures non-linear essentiality effects: the squared mean LOEUF of the "
        "target genes modulates the additive baseline prediction."
    )
    inputs = ["knowledge", "feature"]
    params = {}
    dim = 1

    def _loeuf_table(self, ctx):
        cache = ctx.cache
        key = "_loeuf_squared_e569_table"
        if key in cache:
            return cache[key]

        table = {}
        try:
            k = ctx.knowledge("gene_constraint")
        except Exception:
            k = None

        if k is not None:
            genes = k.get("genes", {}) or {}
            cols = k.get("columns", []) or []
            try:
                idx = list(cols).index("oe_lof_upper")
            except ValueError:
                idx = None
            if idx is not None:
                for g, vals in genes.items():
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
                        table[g] = fv
        cache[key] = table
        return table

    def compute(self, ctx, perts, params):
        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1), dtype=float)

        # additive_response feature (n, n_genes, dim)
        add = ctx.feature("additive_response", perts, None)
        add = np.asarray(add, dtype=float)
        if add.ndim == 3:
            add = add[:, :, 0]
        elif add.ndim != 2:
            add = add.reshape(n, ctx.n_genes)

        loeuf = self._loeuf_table(ctx)

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            vals = [loeuf[g] for g in tg if g in loeuf]
            if not vals:
                continue
            mean_loeuf = float(np.mean(vals))
            coef = mean_loeuf * mean_loeuf
            out[i, :, 0] = coef * add[i, :]

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
