import numpy as np
from genemila.features.api import Feature, register


@register
class TargetPLI(Feature):
    name = "target_pli_e336"
    version = 1
    description = "pLI score of the perturbation target from gnomAD LoF constraint data, median-filled."
    rationale = "pLI measures the probability a gene is intolerant to loss-of-function; essential genes are more likely LoF-intolerant, and their perturbation may cause larger responses."
    inputs = ["gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        out = np.zeros((n_perts, ctx.n_genes, 1), dtype=float)

        knowledge = ctx.knowledge("gene_constraint")
        pli_map = {}
        if knowledge is not None:
            genes_data = knowledge.get("genes", {}) or {}
            columns = knowledge.get("columns", []) or []
            try:
                pli_idx = columns.index("pLI")
            except ValueError:
                pli_idx = None
            if pli_idx is not None:
                for sym, vals in genes_data.items():
                    if vals is None:
                        continue
                    try:
                        v = vals[pli_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        pli_map[sym] = fv

        if pli_map:
            median_val = float(np.median(np.array(list(pli_map.values()), dtype=float)))
        else:
            median_val = 0.0

        for i, p in enumerate(perts):
            target_genes = ctx.target_genes(p)
            val = median_val
            for tg in target_genes:
                if tg in pli_map:
                    val = pli_map[tg]
                    break
            out[i, :, 0] = val

        return out
