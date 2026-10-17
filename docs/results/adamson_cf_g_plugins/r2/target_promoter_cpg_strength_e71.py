import numpy as np
from genemila.features.api import Feature, register


@register
class TargetPromoterCpgStrengthE71(Feature):
    name = "target_promoter_cpg_strength_e71"
    version = 1
    description = "CpG observed/expected ratio in the target gene promoter, broadcast to all genes."
    rationale = ("CpG islands influence transcriptional regulation; target promoter CpG "
                 "content may modulate response magnitude.")
    inputs = ["gene_annotation", "target_genes"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        ann = ctx.knowledge("gene_annotation")
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        if not ann:
            return out

        genes_tbl = ann.get("genes", {}) or {}
        columns = ann.get("columns", []) or []
        try:
            cpg_idx = columns.index("cpg_oe_promoter")
        except ValueError:
            cpg_idx = None

        def get_cpg(sym):
            if cpg_idx is None:
                return np.nan
            vals = genes_tbl.get(sym)
            if vals is None:
                return np.nan
            try:
                v = vals[cpg_idx]
            except (IndexError, TypeError):
                return np.nan
            if v is None:
                return np.nan
            try:
                v = float(v)
            except (TypeError, ValueError):
                return np.nan
            if not np.isfinite(v):
                return np.nan
            return v

        # Memoise per-target-gene lookup across perturbations.
        cache = ctx.cache.setdefault("target_promoter_cpg_strength_e71", {})

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            vals = []
            for sym in tg:
                if sym in cache:
                    vals.append(cache[sym])
                else:
                    v = get_cpg(sym)
                    cache[sym] = v
                    vals.append(v)
            vals = [v for v in vals if np.isfinite(v)]
            if vals:
                out[i, :, 0] = float(np.mean(vals))

        return out
