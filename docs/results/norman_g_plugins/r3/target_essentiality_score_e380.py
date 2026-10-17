import numpy as np
from genemila.features.api import Feature, register


@register
class TargetEssentialityScore(Feature):
    name = "target_essentiality_score_e380"
    version = 1
    description = "Mean LoF-intolerance (1 - LOEUF) of perturbation target genes, broadcast to all genes."
    rationale = "Perturbing essential (LoF-intolerant) genes may drive larger downstream expression changes."
    inputs = ["knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        cache = ctx.cache
        if "e380_scores" not in cache:
            scores = {}
            kc = ctx.knowledge("gene_constraint")
            if kc is not None:
                genes = kc.get("genes", {}) or {}
                cols = kc.get("columns", []) or []
                try:
                    idx = list(cols).index("oe_lof_upper")
                except ValueError:
                    idx = None
                if idx is not None:
                    for g, vals in genes.items():
                        if vals is None:
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
                        if not np.isfinite(fv):
                            continue
                        scores[g] = 1.0 - fv
            cache["e380_scores"] = scores
        scores = cache["e380_scores"]

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            vals = []
            for g in tg:
                if g in scores:
                    vals.append(scores[g])
                else:
                    vals.append(1.0 - 0.5)  # null -> oe_lof_upper 0.5
            if vals:
                m = float(np.mean(vals))
            else:
                m = 1.0 - 0.5
            if not np.isfinite(m):
                m = 0.0
            out[i, :, 0] = m
        return out
