import numpy as np
from genemila.features.api import Feature, register


@register
class GeneLoeufE94(Feature):
    name = "gene_loeuf_e94"
    version = 1
    description = "Per-gene gnomAD LOEUF (oe_lof_upper); lower = more LoF-constrained; median-imputed."
    rationale = "Genes under strong loss-of-function constraint may be more regulated and respond more strongly to pathway perturbations."
    inputs = ["knowledge:gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        vals = np.full(n, np.nan, dtype=float)

        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            cols = kc.get("columns", [])
            try:
                idx = list(cols).index("oe_lof_upper")
            except ValueError:
                idx = None
            genes = kc.get("genes", {}) or {}
            if idx is not None:
                for g, row in genes.items():
                    j = ctx.gene_index.get(g)
                    if j is None:
                        continue
                    if row is None or idx >= len(row):
                        continue
                    v = row[idx]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        vals[j] = fv

        finite = np.isfinite(vals)
        if finite.any():
            fill = float(np.median(vals[finite]))
        else:
            fill = 0.0
        vals[~finite] = fill

        out = np.empty((len(perts), n, 1), dtype=float)
        out[:, :, 0] = vals[None, :]
        return out
