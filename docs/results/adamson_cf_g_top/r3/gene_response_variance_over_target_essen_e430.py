import numpy as np
from genemila.features.api import Feature, register


@register
class GeneResponseVarianceOverTargetEssenE430(Feature):
    name = "gene_response_variance_over_target_essen_e430"
    version = 1
    description = (
        "For each (p,g): ratio of the gene's response variance (across training "
        "perturbations, leaving p out) to (1 + target essentiality score)."
    )
    rationale = (
        "Essential targets may produce more constrained responses; combining gene "
        "response variability with target essentiality captures this interaction."
    )
    inputs = ["train_delta", "gene_constraint"]
    params = {"use_kurtosis": False}
    dim = 1

    def compute(self, ctx, perts, params):
        use_kurtosis = bool(params.get("use_kurtosis", False))
        n_genes = ctx.n_genes

        # --- target essentiality scores from gnomAD LoF constraint ---
        ess_cache = ctx.cache.get("_e430_ess")
        if ess_cache is None:
            ess_cache = {}
            gc = ctx.knowledge("gene_constraint")
            if gc is not None:
                cols = gc.get("columns", [])
                genes_tbl = gc.get("genes", {}) or {}
                # prefer LOEUF (oe_lof_upper); lower = more LoF-intolerant = more essential
                if "oe_lof_upper" in cols:
                    idx = cols.index("oe_lof_upper")
                    for sym, vals in genes_tbl.items():
                        if vals is None:
                            continue
                        v = vals[idx] if idx < len(vals) else None
                        if v is None:
                            continue
                        try:
                            ess_cache[sym] = float(v)
                        except (TypeError, ValueError):
                            continue
                elif "pLI" in cols:
                    idx = cols.index("pLI")
                    for sym, vals in genes_tbl.items():
                        if vals is None:
                            continue
                        v = vals[idx] if idx < len(vals) else None
                        if v is None:
                            continue
                        try:
                            ess_cache[sym] = float(v)
                        except (TypeError, ValueError):
                            continue
            ctx.cache["_e430_ess"] = ess_cache

        # helper: essentiality for a perturbation via its target genes
        def target_ess(p):
            tg = ctx.target_genes(p)
            if not tg:
                return 0.0
            vals = [ess_cache.get(t, 0.0) for t in tg]
            # mean over targets; if LOEUF-like small values, invert to a positive score
            m = float(np.mean(vals)) if vals else 0.0
            return m

        out = np.zeros((len(perts), n_genes, 1))
        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            if d.shape[0] == 0:
                continue
            if use_kurtosis:
                mu = d.mean(axis=0)
                centered = d - mu
                var = (centered ** 2).mean(axis=0)
                var = np.where(var > 0, var, 1e-12)
                kurt = (centered ** 4).mean(axis=0) / (var ** 2)
                stat = kurt
            else:
                stat = d.var(axis=0)

            e = target_ess(p)
            denom = 1.0 + abs(e)
            out[i, :, 0] = stat / denom

        # ensure finite
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
