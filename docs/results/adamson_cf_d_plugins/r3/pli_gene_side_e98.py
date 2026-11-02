import numpy as np
from genemila.features.api import Feature, register


@register
class PliGeneSideE98(Feature):
    name = "pli_gene_side_e98"
    version = 1
    description = "Per-gene pLI (LoF intolerance), missing imputed, z-scored across genes."
    rationale = (
        "pLI measures intolerance to loss-of-function; genes under strong purifying "
        "selection may be more buffered against expression changes, leading to smaller "
        "deltas. Encodes a gene-level constraint weight independent of the perturbation."
    )
    inputs = ["knowledge:gene_constraint"]
    params = {"impute": 0.0}
    dim = 1

    def compute(self, ctx, perts, params):
        impute = float(params.get("impute", 0.0))
        n_genes = ctx.n_genes
        values = np.full(n_genes, impute, dtype=np.float64)

        cache_key = "_pli_gene_side_e98_values"
        cached = ctx.cache.get(cache_key)
        if cached is not None:
            values = cached
        else:
            kc = ctx.knowledge("gene_constraint")
            if kc is not None:
                cols = kc.get("columns", [])
                # locate the pLI column (case-insensitive)
                pli_idx = None
                for j, c in enumerate(cols):
                    if str(c).lower() == "pli":
                        pli_idx = j
                        break
                genes_tbl = kc.get("genes", {}) or {}
                if pli_idx is not None:
                    for g, row in genes_tbl.items():
                        gi = ctx.gene_index.get(g)
                        if gi is None:
                            continue
                        if row is None:
                            continue
                        try:
                            val = row[pli_idx]
                        except (IndexError, TypeError):
                            continue
                        if val is None:
                            continue
                        try:
                            fval = float(val)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fval):
                            values[gi] = fval
            # z-score across genes
            mu = values.mean()
            sd = values.std()
            if sd > 0 and np.isfinite(sd):
                values = (values - mu) / sd
            else:
                values = values - mu
            values = np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)
            ctx.cache[cache_key] = values

        out = np.empty((len(perts), n_genes, 1), dtype=np.float64)
        out[:, :, 0] = values[None, :]
        return out
