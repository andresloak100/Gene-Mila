import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGeneLoeufRatioE477(Feature):
    name = "target_gene_loeuf_ratio_e477"
    version = 1
    description = "Ratio of target LOEUF to gene LOEUF (log ratio, clipped)."
    rationale = ("Genes with very different constraint levels may respond differently "
                 "to perturbation; the ratio captures directionality of constraint "
                 "asymmetry between target and gene, complementing the product feature.")
    inputs = ["knowledge:gene_constraint", "target_indices"]
    params = {"clip": True, "clip_min": 0.1, "clip_max": 10.0, "use_log": True}
    dim = 1

    def _loeuf_map(self, ctx):
        cache = ctx.cache
        key = "_e477_loeuf"
        if key in cache:
            return cache[key]
        loeuf = np.full(ctx.n_genes, np.nan, dtype=np.float64)
        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            genes = kc.get("genes", {})
            columns = kc.get("columns", [])
            try:
                idx = list(columns).index("oe_lof_upper")
            except (ValueError, TypeError):
                idx = None
            if idx is not None:
                for g, vals in genes.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None or vals is None:
                        continue
                    try:
                        v = vals[idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv) and fv > 0:
                        loeuf[gi] = fv
        cache[key] = loeuf
        return loeuf

    def compute(self, ctx, perts, params):
        clip = bool(params.get("clip", True))
        cmin = float(params.get("clip_min", 0.1))
        cmax = float(params.get("clip_max", 10.0))
        use_log = bool(params.get("use_log", True))

        loeuf = self._loeuf_map(ctx)
        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1), dtype=np.float64)

        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            t_vals = [loeuf[j] for j in t_idx if np.isfinite(loeuf[j])]
            if len(t_vals) == 0:
                continue
            t_loeuf = float(np.mean(t_vals))
            if not np.isfinite(t_loeuf) or t_loeuf <= 0:
                continue
            with np.errstate(divide="ignore", invalid="ignore"):
                ratio = t_loeuf / loeuf
            ratio = np.where(np.isfinite(loeuf) & (loeuf > 0), ratio, np.nan)
            if clip:
                ratio = np.clip(ratio, cmin, cmax)
            if use_log:
                ratio = np.log(ratio)
            ratio = np.where(np.isfinite(ratio), ratio, 0.0)
            out[i, :, 0] = ratio

        return out
