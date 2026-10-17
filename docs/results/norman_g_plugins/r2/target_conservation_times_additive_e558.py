import numpy as np
from genemila.features.api import Feature, register


@register
class TargetConservationTimesAdditiveE558(Feature):
    name = "target_conservation_times_additive_e558"
    version = 1
    description = (
        "Product of additive_response and the mean conservation of p's target genes, "
        "where conservation is derived from gnomAD LoF constraint (inverted LOEUF)."
    )
    rationale = (
        "Evolutionarily conserved (LoF-intolerant) genes may mediate stronger regulatory "
        "effects; scaling the additive prediction by target conservation can modulate "
        "predicted response magnitude."
    )
    inputs = ["additive_response", "gene_constraint"]
    params = {"conservation_metric": "loeuf_inverted"}
    dim = 1

    def _conservation_scores(self, ctx, params):
        cache = ctx.cache
        key = ("e558_conservation", params.get("conservation_metric", "loeuf_inverted"))
        if key in cache:
            return cache[key]

        metric = params.get("conservation_metric", "loeuf_inverted")
        cons = np.full(ctx.n_genes, np.nan, dtype=np.float64)

        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            genes_tbl = kc.get("genes", {}) or {}
            columns = kc.get("columns", []) or []

            def col_idx(name):
                try:
                    return columns.index(name)
                except ValueError:
                    return None

            i_loeuf = col_idx("oe_lof_upper")
            i_pli = col_idx("pLI")
            if i_pli is None:
                i_pli = col_idx("pli")

            for gi, g in enumerate(ctx.genes):
                vals = genes_tbl.get(g)
                if vals is None:
                    continue
                if metric == "pli":
                    if i_pli is not None and i_pli < len(vals) and vals[i_pli] is not None:
                        try:
                            cons[gi] = float(vals[i_pli])
                        except (TypeError, ValueError):
                            pass
                else:  # loeuf_inverted
                    if i_loeuf is not None and i_loeuf < len(vals) and vals[i_loeuf] is not None:
                        try:
                            cons[gi] = 1.0 - float(vals[i_loeuf])
                        except (TypeError, ValueError):
                            pass

        cache[key] = cons
        return cons

    def compute(self, ctx, perts, params):
        cons = self._conservation_scores(ctx, params)
        fallback = np.nanmean(cons) if np.any(np.isfinite(cons)) else 0.0
        if not np.isfinite(fallback):
            fallback = 0.0

        additive = ctx.feature("additive_response", perts, params=None)
        additive = np.asarray(additive, dtype=np.float64)
        if additive.ndim == 2:
            additive = additive[:, :, None]

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=np.float64)

        for i, p in enumerate(perts):
            tgt = ctx.target_indices(p)
            if tgt:
                vals = cons[tgt]
                finite = vals[np.isfinite(vals)]
                mean_cons = float(finite.mean()) if finite.size > 0 else fallback
            else:
                mean_cons = fallback
            out[i, :, 0] = additive[i, :, 0] * mean_cons

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
