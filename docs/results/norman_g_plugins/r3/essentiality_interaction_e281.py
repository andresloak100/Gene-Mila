import numpy as np
from genemila.features.api import Feature, register


@register
class EssentialityInteractionE281(Feature):
    name = "essentiality_interaction_e281"
    version = 1
    description = ("Product of normalized LoF-intolerance score of the perturbation's "
                   "target gene(s) and the normalized LoF-intolerance score of gene g.")
    rationale = ("Essential (LoF-intolerant) genes may mediate stronger downstream effects "
                 "when perturbed; the response of other essential genes may be amplified.")
    inputs = ["knowledge"]
    params = {"normalization": "minmax"}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        norm = params.get("normalization", "minmax")

        # Build per-gene raw LoF-intolerance score: 1 - LOEUF (higher = more intolerant).
        raw = np.full(n_genes, np.nan, dtype=float)
        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            cols = kc.get("columns", [])
            genes_tbl = kc.get("genes", {})
            try:
                loeuf_idx = cols.index("oe_lof_upper")
            except ValueError:
                loeuf_idx = None
            if loeuf_idx is not None:
                for g, col in ctx.gene_index.items():
                    vals = genes_tbl.get(g)
                    if vals is None:
                        continue
                    try:
                        v = vals[loeuf_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        v = float(v)
                    except (TypeError, ValueError):
                        continue
                    if not np.isfinite(v):
                        continue
                    raw[col] = 1.0 - v

        # Normalize to [0,1].
        score = np.zeros(n_genes, dtype=float)
        finite_mask = np.isfinite(raw)
        if finite_mask.any():
            vals = raw[finite_mask]
            if norm == "minmax":
                lo, hi = vals.min(), vals.max()
                if hi > lo:
                    score[finite_mask] = (vals - lo) / (hi - lo)
                else:
                    score[finite_mask] = 0.5
            else:
                # fallback: rank-based normalization
                order = np.argsort(np.argsort(vals))
                denom = max(len(vals) - 1, 1)
                score[finite_mask] = order / denom

        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if not t_idx:
                continue
            t_scores = score[t_idx]
            t_score = float(t_scores.mean())
            out[i, :, 0] = t_score * score
        return out
