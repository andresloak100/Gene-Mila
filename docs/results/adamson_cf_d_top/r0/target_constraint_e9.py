import numpy as np
from genemila.features.api import Feature, register


@register
class TargetConstraintE9(Feature):
    name = "target_constraint_e9"
    version = 1
    description = "LOEUF (or pLI) of the targeted gene, broadcast to all genes."
    rationale = ("Perturbing genes intolerant to loss-of-function (low LOEUF / high pLI) "
                 "causes stronger downstream expression changes.")
    inputs = ["gene_constraint"]
    params = {"constraint_metric": "oe_lof_upper"}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        metric = params.get("constraint_metric", "oe_lof_upper")
        kc = ctx.knowledge("gene_constraint")

        # Build gene -> value lookup for the requested metric.
        values = {}
        if kc is not None:
            cols = kc.get("columns", [])
            genes_tbl = kc.get("genes", {}) or {}
            if metric in cols:
                col_idx = cols.index(metric)
                for sym, row in genes_tbl.items():
                    if row is None:
                        continue
                    try:
                        v = row[col_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        v = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(v):
                        values[sym] = v

        # Fallback fill value: mean of available metric values (or 0).
        if values:
            fill = float(np.mean(list(values.values())))
        else:
            fill = 0.0

        for i, p in enumerate(perts):
            v = None
            for tg in ctx.target_genes(p):
                if tg in values:
                    v = values[tg]
                    break
            if v is None:
                v = fill
            out[i, :, 0] = v

        # Ensure finite.
        out[~np.isfinite(out)] = 0.0
        return out
