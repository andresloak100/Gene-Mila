import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGeneEssentialityProduct(Feature):
    name = "target_gene_essentiality_product_e203"
    version = 1
    description = "Product of mean target-gene LOEUF and gene g's LOEUF (essentiality signal)."
    rationale = ("Essential genes (low LOEUF) are network hubs; combining target essentiality "
                 "with a gene's own essentiality captures synergistic vulnerability.")
    inputs = ["control_mean", "gene_constraint"]
    params = {"impute": "median"}
    dim = 1

    def _loeuf_vector(self, ctx):
        cache = ctx.cache
        key = "_e203_loeuf_vec"
        if key in cache:
            return cache[key]
        vec = np.full(ctx.n_genes, np.nan, dtype=float)
        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            genes = kc.get("genes", {})
            cols = kc.get("columns", [])
            try:
                idx = cols.index("oe_lof_upper")
            except ValueError:
                idx = None
            if idx is not None:
                for gi, g in enumerate(ctx.genes):
                    vals = genes.get(g)
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
                        vec[gi] = fv
        cache[key] = vec
        return vec

    def compute(self, ctx, perts, params):
        loeuf = self._loeuf_vector(ctx)
        finite = np.isfinite(loeuf)
        if finite.any():
            fill = float(np.median(loeuf[finite]))
        else:
            fill = 1.0
        loeuf_filled = np.where(finite, loeuf, fill)

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if len(t_idx) == 0:
                mean_t = fill
            else:
                mean_t = float(np.mean(loeuf_filled[t_idx]))
            out[i, :, 0] = mean_t * loeuf_filled
        return out
