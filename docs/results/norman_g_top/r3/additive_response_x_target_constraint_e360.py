import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveResponseXTargetConstraintE360(Feature):
    name = "additive_response_x_target_constraint_e360"
    version = 1
    description = "Product of additive_response and normalized LoF-intolerance of target gene(s)."
    rationale = "Targets that are LoF-intolerant are tightly regulated; their perturbation may produce a larger additive response."
    inputs = ["control_cells", "gene_constraint", "additive_response"]
    params = {"constraint_metric": "loeuf", "pair_combine": "mean"}
    dim = 1

    def _constraint_scores(self, ctx, params):
        cache = ctx.cache
        key = ("e360_constraint", params.get("constraint_metric", "loeuf"))
        if key in cache:
            return cache[key]

        metric = params.get("constraint_metric", "loeuf")
        kc = ctx.knowledge("gene_constraint")
        scores = np.full(ctx.n_genes, np.nan, dtype=float)

        if kc is not None:
            cols = kc.get("columns", [])
            genes_tbl = kc.get("genes", {})
            if metric == "pli" and "pLI" in cols:
                idx = cols.index("pLI")
            elif "oe_lof_upper" in cols:
                idx = cols.index("oe_lof_upper")
            else:
                idx = None

            if idx is not None:
                for g, col in ctx.gene_index.items():
                    vals = genes_tbl.get(g)
                    if vals is None:
                        continue
                    v = vals[idx]
                    if v is None:
                        continue
                    try:
                        v = float(v)
                    except (TypeError, ValueError):
                        continue
                    if not np.isfinite(v):
                        continue
                    if metric == "pli":
                        scores[col] = v
                    else:
                        # LOEUF: lower = more intolerant -> constraint = 1 - LOEUF
                        scores[col] = 1.0 - v

        # Fallback / fill: use mean of defined scores; if none, 0.5
        finite = np.isfinite(scores)
        fill = scores[finite].mean() if finite.any() else 0.5
        scores[~finite] = fill

        # Clip to a reasonable range
        scores = np.clip(scores, 0.0, 1.0)
        cache[key] = scores
        return scores

    def compute(self, ctx, perts, params):
        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1), dtype=float)
        if n == 0:
            return out

        scores = self._constraint_scores(ctx, params)
        pair_combine = params.get("pair_combine", "mean")

        try:
            add = ctx.feature("additive_response", perts, None)
            add = np.asarray(add, dtype=float)
            if add.ndim == 3:
                add = add[:, :, 0]
        except Exception:
            add = np.zeros((n, ctx.n_genes), dtype=float)

        for i, p in enumerate(perts):
            tgt = ctx.target_indices(p)
            if len(tgt) == 0:
                out[i, :, 0] = 0.0
                continue
            vals = scores[np.asarray(tgt, dtype=int)]
            if len(vals) == 1:
                c = float(vals[0])
            else:
                if pair_combine == "max":
                    c = float(np.max(vals))
                else:
                    c = float(np.mean(vals))
            out[i, :, 0] = add[i] * c

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
