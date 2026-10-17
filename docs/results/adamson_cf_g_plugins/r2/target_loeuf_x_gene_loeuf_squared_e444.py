import numpy as np
from genemila.features.api import Feature, register

@register
class TargetLoeufXGeneLoeufSquaredE444(Feature):
    name = "target_loeuf_x_gene_loeuf_squared_e444"
    version = 1
    description = "Product of target LOEUF and gene LOEUF, squared to emphasize extreme combinations."
    rationale = ("LoF-intolerant genes are under stronger regulatory control; perturbing an intolerant "
                 "target may propagate to other intolerant genes. Squaring emphasizes extreme combinations.")
    inputs = ["knowledge", "target_indices"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        # Load gnomAD constraint table once.
        cache_key = "_loeuf_lookup_e444"
        if cache_key not in ctx.cache:
            lookup = {}
            ka = ctx.knowledge("gene_constraint")
            if ka is not None:
                cols = ka.get("columns", [])
                genes = ka.get("genes", {})
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
                            lookup[g] = fv
            ctx.cache[cache_key] = lookup
        lookup = ctx.cache[cache_key]

        # Per-gene LOEUF vector.
        gene_loeuf = np.zeros(ctx.n_genes, dtype=float)
        for gi, g in enumerate(ctx.genes):
            v = lookup.get(g)
            if v is not None:
                gene_loeuf[gi] = v

        for i, p in enumerate(perts):
            tidx = ctx.target_indices(p)
            if not tidx:
                continue
            # Average LOEUF over targeted genes (usually one).
            tv = gene_loeuf[tidx]
            tv = tv[np.isfinite(tv)]
            if tv.size == 0:
                continue
            target_loeuf = float(tv.mean())
            if not np.isfinite(target_loeuf):
                continue
            base = target_loeuf * gene_loeuf  # (n_genes,)
            out[i, :, 0] = base * base

        out[~np.isfinite(out)] = 0.0
        return out
