import numpy as np
from genemila.features.api import Feature, register


@register
class ReplogleAdditiveXTargetPromoterGC(Feature):
    name = "replogle_additive_x_target_promoter_gc_e328"
    version = 1
    description = "Sum over p's targets of sign-corrected Replogle delta times target promoter GC."
    rationale = "Promoter GC content modulates CRISPRa response; weighting target deltas by it captures target-specific modulation."
    inputs = ["knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        gc = {}
        sign = -1.0
        repl_perts = {}

        repl = ctx.knowledge("replogle2022_k562")
        if repl is not None:
            s = repl.get("sign", -1)
            try:
                sign = float(s)
            except (TypeError, ValueError):
                sign = -1.0
            if not np.isfinite(sign):
                sign = -1.0
            repl_perts = repl.get("perts", {}) or {}

        if ann is not None:
            cols = ann.get("columns", []) or []
            genes = ann.get("genes", {}) or {}
            gi = None
            try:
                gi = cols.index("gc_promoter")
            except (ValueError, AttributeError):
                gi = None
            if gi is not None:
                for g, vals in genes.items():
                    if vals is None:
                        continue
                    try:
                        v = vals[gi]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        gc[g] = fv

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue
            total = np.zeros(ctx.n_genes, dtype=float)
            for t in targets:
                w = gc.get(t, 0.0)
                if w == 0.0 or not np.isfinite(w):
                    continue
                rec = repl_perts.get(t)
                if rec is None:
                    continue
                d = rec.get("delta")
                if d is None:
                    continue
                try:
                    arr = np.asarray(d, dtype=float)
                except (TypeError, ValueError):
                    continue
                if arr.size != ctx.n_genes:
                    continue
                arr = np.where(np.isfinite(arr), arr, 0.0)
                total += sign * w * arr
            out[i, :, 0] = np.where(np.isfinite(total), total, 0.0)

        out = np.where(np.isfinite(out), out, 0.0)
        return out
