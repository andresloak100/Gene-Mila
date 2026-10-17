import numpy as np
from genemila.features.api import Feature, register


@register
class ConstraintInteractionE462(Feature):
    name = "constraint_interaction_e462"
    version = 1
    description = ("Interaction between LOEUF of perturbation target gene(s) and LOEUF of "
                   "responding gene g (product or sum), averaged over pair targets.")
    rationale = ("Genes under strong loss-of-function constraint may have more robust regulatory "
                 "networks; the product of target and responder constraint captures this interaction.")
    inputs = ["gene_constraint"]
    params = {"interaction": "product"}
    dim = 1

    def _get_loeuf(self, ctx, symbol):
        """Return LOEUF (oe_lof_upper) for a gene symbol, or NaN if missing."""
        cache = ctx.cache.setdefault("_e462_loeuf", {})
        if symbol in cache:
            return cache[symbol]
        val = np.nan
        gc = ctx.knowledge("gene_constraint")
        if gc is not None:
            genes = gc.get("genes", {})
            cols = gc.get("columns", [])
            if symbol in genes:
                try:
                    idx = cols.index("oe_lof_upper")
                except (ValueError, AttributeError):
                    idx = None
                if idx is not None:
                    row = genes[symbol]
                    if row is not None and idx < len(row):
                        v = row[idx]
                        if v is not None:
                            try:
                                fv = float(v)
                                if np.isfinite(fv):
                                    val = fv
                            except (TypeError, ValueError):
                                pass
        cache[symbol] = val
        return val

    def compute(self, ctx, perts, params):
        interaction = params.get("interaction", "product")
        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1), dtype=float)

        # Precompute LOEUF for every measured gene once.
        gene_loeuf = np.full(ctx.n_genes, np.nan, dtype=float)
        for gi, gsym in enumerate(ctx.genes):
            gene_loeuf[gi] = self._get_loeuf(ctx, gsym)

        # Fallback for missing gene LOEUF: use column mean of observed values.
        if np.any(np.isfinite(gene_loeuf)):
            g_mean = float(np.nanmean(gene_loeuf))
        else:
            g_mean = 1.0
        gene_loeuf_filled = np.where(np.isfinite(gene_loeuf), gene_loeuf, g_mean)

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue
            t_vals = []
            for t in targets:
                v = self._get_loeuf(ctx, t)
                if not np.isfinite(v):
                    v = g_mean
                t_vals.append(v)
            t_arr = np.asarray(t_vals, dtype=float)

            if interaction == "sum":
                # For pairs: sum over targets, then sum with g.
                t_stat = t_arr.sum()
                out[i, :, 0] = t_stat + gene_loeuf_filled
            else:
                # product: average over targets of (target * g)
                out[i, :, 0] = t_arr.mean() * gene_loeuf_filled

        return out
