import numpy as np
from genemila.features.api import Feature, register


@register
class EssentialityInteractionE803(Feature):
    name = "essentiality_interaction_e803"
    version = 1
    description = "Product of target essentiality score and gene g essentiality score (LOEUF-based)."
    rationale = ("Essentiality reflects gene importance; the interaction between target and "
                 "response-gene essentiality may capture synergistic perturbation effects.")
    inputs = ["knowledge", "target_indices"]
    params = {"impute": "median"}
    dim = 1

    def _essentiality_vector(self, ctx, params):
        cache = ctx.cache
        key = "essentiality_interaction_e803_scores"
        if key in cache:
            return cache[key]

        n_genes = ctx.n_genes
        scores = np.full(n_genes, np.nan, dtype=float)

        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            cols = kc.get("columns", [])
            genes = kc.get("genes", {})
            oe_idx = None
            pli_idx = None
            for j, c in enumerate(cols):
                cl = str(c).lower()
                if "oe_lof_upper" in cl:
                    oe_idx = j
                elif cl == "pli" or "pli" in cl:
                    if pli_idx is None:
                        pli_idx = j

            for g in ctx.genes:
                vals = genes.get(g)
                if vals is None:
                    continue
                s = np.nan
                if oe_idx is not None and oe_idx < len(vals) and vals[oe_idx] is not None:
                    try:
                        v = float(vals[oe_idx])
                        if np.isfinite(v):
                            s = -v  # low LOEUF = high essentiality
                    except (TypeError, ValueError):
                        pass
                if not np.isfinite(s) and pli_idx is not None and pli_idx < len(vals) \
                        and vals[pli_idx] is not None:
                    try:
                        v = float(vals[pli_idx])
                        if np.isfinite(v):
                            s = v  # high pLI = high essentiality
                    except (TypeError, ValueError):
                        pass
                if np.isfinite(s):
                    scores[ctx.gene_index[g]] = s

        # impute missing
        finite_mask = np.isfinite(scores)
        if finite_mask.any():
            fill = np.nanmedian(scores[finite_mask])
        else:
            fill = 0.0
        scores = np.where(finite_mask, scores, fill)

        # standardize for stable product scale
        mu = scores.mean()
        sd = scores.std()
        if sd > 0:
            scores = (scores - mu) / sd
        else:
            scores = scores - mu

        cache[key] = scores
        return scores

    def compute(self, ctx, perts, params):
        scores = self._essentiality_vector(ctx, params)
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if tgt_idx:
                tgt_scores = scores[np.asarray(tgt_idx, dtype=int)]
                tgt_score = float(np.mean(tgt_scores))
            else:
                tgt_score = float(np.median(scores))
            out[i, :, 0] = tgt_score * scores

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
