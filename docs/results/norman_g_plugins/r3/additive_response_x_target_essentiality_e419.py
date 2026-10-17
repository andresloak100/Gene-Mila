import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveResponseXTargetEssentialityE419(Feature):
    name = "additive_response_x_target_essentiality_e419"
    version = 1
    description = ("Product of the additive response baseline and the mean normalized "
                   "essentiality score (1 - LOEUF) of the perturbation's target gene(s).")
    rationale = ("Perturbing LoF-intolerant (essential) genes may yield stronger responses; "
                 "this interaction scales the additive baseline by target essentiality.")
    inputs = ["train_delta", "gene_constraint"]
    params = {"essentiality_metric": "1_minus_loeuf"}
    dim = 1

    def _essentiality_map(self, ctx, params):
        cache = ctx.cache
        key = ("ess_map_e419", params.get("essentiality_metric", "1_minus_loeuf"))
        if key in cache:
            return cache[key]
        ess = np.zeros(ctx.n_genes, dtype=float)
        gc = ctx.knowledge("gene_constraint")
        if gc is not None:
            cols = gc.get("columns", [])
            genes_tbl = gc.get("genes", {})
            loeuf_idx = None
            for j, c in enumerate(cols):
                if c == "oe_lof_upper":
                    loeuf_idx = j
                    break
            if loeuf_idx is not None:
                for g, vals in genes_tbl.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None or vals is None:
                        continue
                    v = vals[loeuf_idx] if loeuf_idx < len(vals) else None
                    if v is None:
                        continue
                    try:
                        v = float(v)
                    except (TypeError, ValueError):
                        continue
                    if not np.isfinite(v):
                        continue
                    # essentiality = 1 - LOEUF, clipped to [0, 1]
                    ess[gi] = float(np.clip(1.0 - v, 0.0, 1.0))
        cache[key] = ess
        return ess

    def compute(self, ctx, perts, params):
        ess = self._essentiality_map(ctx, params)
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if len(tgt_idx) == 0:
                continue
            tgt_ess = ess[np.asarray(tgt_idx, dtype=int)]
            mean_ess = float(tgt_ess.mean()) if tgt_ess.size > 0 else 0.0
            _, d = ctx.train_delta(exclude=p)
            add = d.mean(axis=0)
            out[i, :, 0] = add * mean_ess
        out[~np.isfinite(out)] = 0.0
        return out
