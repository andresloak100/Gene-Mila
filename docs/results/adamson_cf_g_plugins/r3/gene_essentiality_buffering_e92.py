import numpy as np
from genemila.features.api import Feature, register


@register
class GeneEssentialityBufferingE92(Feature):
    name = "gene_essentiality_buffering_e92"
    version = 1
    description = (
        "Per-gene essentiality (LOEUF or pLI) of the response gene g, median-filled, "
        "optionally interacted with the target gene's essentiality."
    )
    rationale = (
        "Essential (highly LoF-constrained) genes are tightly buffered, so their "
        "expression changes less after perturbation; the constraint of the response "
        "gene g should therefore predict a smaller-magnitude delta."
    )
    inputs = ["knowledge"]
    params = {
        "constraint_metric": "oe_lof_upper",
        "interact_with_target": False,
    }
    dim = 1

    def _load_metric(self, ctx, metric):
        """Return (values dict gene->float, median fill)."""
        cache = ctx.cache
        key = ("e92_constraint", metric)
        if key in cache:
            return cache[key]

        vals = {}
        median = 0.0
        kn = ctx.knowledge("gene_constraint")
        if kn is not None:
            cols = kn.get("columns", [])
            genes = kn.get("genes", {})
            if metric in cols:
                ci = cols.index(metric)
                raw = []
                for g, row in genes.items():
                    if row is None:
                        continue
                    try:
                        v = row[ci]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if not np.isfinite(fv):
                        continue
                    vals[g] = fv
                    raw.append(fv)
                if raw:
                    median = float(np.median(raw))
        cache[key] = (vals, median)
        return cache[key]

    def compute(self, ctx, perts, params):
        metric = params.get("constraint_metric", "oe_lof_upper")
        interact = bool(params.get("interact_with_target", False))

        vals, median = self._load_metric(ctx, metric)

        # Per-gene essentiality vector aligned to ctx.genes
        gene_ess = np.full(ctx.n_genes, median, dtype=np.float64)
        for i, g in enumerate(ctx.genes):
            v = vals.get(g)
            if v is not None and np.isfinite(v):
                gene_ess[i] = v

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=np.float64)

        for i, p in enumerate(perts):
            if interact:
                tvals = []
                for tg in ctx.target_genes(p):
                    v = vals.get(tg)
                    if v is not None and np.isfinite(v):
                        tvals.append(v)
                t_ess = float(np.mean(tvals)) if tvals else median
                out[i, :, 0] = gene_ess * t_ess
            else:
                out[i, :, 0] = gene_ess

        out[~np.isfinite(out)] = 0.0
        return out
