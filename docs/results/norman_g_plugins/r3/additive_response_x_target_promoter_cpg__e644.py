import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveResponseXTargetPromoterCpg(Feature):
    name = "additive_response_x_target_promoter_cpg__e644"
    version = 1
    description = ("Product of additive_response and the mean CpG observed/expected "
                   "ratio in the promoter regions of the perturbation's target genes.")
    rationale = ("CRISPRa efficiency depends on promoter accessibility; CpG-rich "
                 "promoters may modulate activation strength, scaling the additive "
                 "response by the target promoters' CpG content.")
    inputs = ["gene_annotation", "feature:additive_response"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))

        # additive_response baseline (n_perts, n_genes, 1)
        add = ctx.feature("additive_response", perts)
        if add.ndim == 2:
            add = add[:, :, None]

        # Load CpG observed/expected promoter density per gene.
        ann = ctx.knowledge("gene_annotation")
        cpg_col = None
        if ann is not None:
            cols = ann.get("columns", [])
            for cand in ("cpg_oe_promoter", "gc_promoter"):
                if cand in cols:
                    cpg_col = cand
                    break
        if cpg_col is None:
            # No usable annotation; feature degenerates to zero.
            return out

        col_idx = ann["columns"].index(cpg_col)
        gene_vals = ann.get("genes", {})

        # Per-gene CpG value array aligned to ctx.genes; NaN where missing.
        cpg = np.full(ctx.n_genes, np.nan, dtype=float)
        for g, name in enumerate(ctx.genes):
            vals = gene_vals.get(name)
            if vals is None:
                continue
            try:
                v = vals[col_idx]
            except (IndexError, TypeError):
                continue
            if v is not None:
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv):
                    cpg[g] = fv

        cache = ctx.cache
        cache_key = ("e644_cpg", cpg_col)
        if cache_key not in cache:
            cache[cache_key] = cpg
        cpg = cache[cache_key]

        # Global fallback mean over measured genes.
        finite_mask = np.isfinite(cpg)
        global_mean = float(cpg[finite_mask].mean()) if finite_mask.any() else 0.0

        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if not t_idx:
                mean_cpg = global_mean
            else:
                vals = cpg[np.asarray(t_idx, dtype=int)]
                vals = vals[np.isfinite(vals)]
                mean_cpg = float(vals.mean()) if vals.size > 0 else global_mean
            out[i, :, 0] = add[i, :, 0] * mean_cpg

        # Ensure finite values only.
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
