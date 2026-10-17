import numpy as np
from genemila.features.api import Feature, register


@register
class TargetPromoterAccessibilityProxyE379(Feature):
    name = "target_promoter_accessibility_proxy_e379"
    version = 1
    description = ("Mean over target genes of a promoter accessibility proxy built from "
                   "normalized gc_promoter and cpg_oe_promoter, broadcast to all genes.")
    rationale = ("GC-rich, CpG-depleted promoters are nucleosome-depleted and accessible, "
                 "so CRISPRa at such targets yields larger effects. Averaging over both "
                 "targets of a pair gives an order-independent perturbation-level score.")
    inputs = ["knowledge"]
    params = {}
    dim = 1

    def _build_scores(self, ctx):
        cache = ctx.cache
        key = "_e379_scores"
        if key in cache:
            return cache[key]

        ann = ctx.knowledge("gene_annotation")
        n = ctx.n_genes
        gc = np.full(n, np.nan, dtype=float)
        cpg = np.full(n, np.nan, dtype=float)

        if ann is not None:
            cols = ann.get("columns", [])
            genes = ann.get("genes", {})
            try:
                i_gc = cols.index("gc_promoter")
            except ValueError:
                i_gc = None
            try:
                i_cpg = cols.index("cpg_oe_promoter")
            except ValueError:
                i_cpg = None
            if i_gc is not None or i_cpg is not None:
                for gi, g in enumerate(ctx.genes):
                    vals = genes.get(g)
                    if vals is None:
                        continue
                    if i_gc is not None and i_gc < len(vals):
                        v = vals[i_gc]
                        if v is not None:
                            gc[gi] = float(v)
                    if i_cpg is not None and i_cpg < len(vals):
                        v = vals[i_cpg]
                        if v is not None:
                            cpg[gi] = float(v)

        def norm01(x):
            out = np.zeros_like(x)
            m = np.isfinite(x)
            if not m.any():
                return out
            v = x[m]
            lo = np.min(v)
            hi = np.max(v)
            if hi > lo:
                out[m] = (v - lo) / (hi - lo)
            else:
                out[m] = 0.5
            return out

        gc_n = norm01(gc)
        cpg_n = norm01(cpg)
        # combine; cpg_oe_promoter lower = more CpG-depleted = more accessible
        score = 0.5 * gc_n + 0.5 * (1.0 - cpg_n)
        cache[key] = score
        return score

    def compute(self, ctx, perts, params):
        score = self._build_scores(ctx)
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            idx = ctx.target_indices(p)
            if idx:
                val = float(np.mean(score[np.asarray(idx, dtype=int)]))
            else:
                val = 0.0
            if not np.isfinite(val):
                val = 0.0
            out[i, :, 0] = val
        return out
