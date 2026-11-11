import numpy as np
from genemila.features.api import Feature, register

@register
class TargetPliE67(Feature):
    name = "target_pli_e67"
    version = 1
    description = "pLI value of the targeted gene, broadcast to all genes."
    rationale = ("High pLI genes are essential and their perturbation triggers stronger "
                 "transcriptional responses.")
    inputs = ["knowledge:gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        kc = ctx.knowledge("gene_constraint")
        if not kc:
            return out
        genes_tbl = kc.get("genes", {}) or {}
        columns = kc.get("columns", []) or []
        try:
            pli_idx = columns.index("pLI")
        except ValueError:
            return out

        # cache parsed pLI per symbol
        cache = ctx.cache
        pli_map = cache.get("_pli_map_e67")
        if pli_map is None:
            pli_map = {}
            for sym, vals in genes_tbl.items():
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
            cache["_pli_map_e67"] = pli_map

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            if not tg:
                continue
            vals = [pli_map[g] for g in tg if g in pli_map]
            if vals:
                out[i, :, 0] = float(np.mean(vals))
        return out
