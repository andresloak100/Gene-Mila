import numpy as np
from genemila.features.api import Feature, register


@register
class EssentialityWeightedResponseSimilarity(Feature):
    name = "essentiality_weighted_response_similarit_e368"
    version = 1
    description = ("Product of target_response_similarity_to_mean_e110 and an essentiality "
                   "score (e.g. inverse LOEUF) averaged over the perturbation's target genes.")
    rationale = ("Essential genes may have stronger or more conserved transcriptional responses; "
                 "weighting target response similarity by essentiality captures this.")
    inputs = ["gene_constraint", "feature:target_response_similarity_to_mean_e110"]
    params = {"essentiality_metric": "inverse_loeuf"}
    dim = 1

    def _essentiality(self, ctx, params):
        cache = ctx.cache
        key = ("ess_scores", params.get("essentiality_metric", "inverse_loeuf"))
        if key in cache:
            return cache[key]

        metric = params.get("essentiality_metric", "inverse_loeuf")
        scores = np.ones(ctx.n_genes, dtype=float)

        data = ctx.knowledge("gene_constraint")
        if data is not None:
            cols = list(data.get("columns", []))
            genes_tbl = data.get("genes", {}) or {}
            flags = data.get("flags", {}) or {}

            def col_idx(name):
                try:
                    return cols.index(name)
                except ValueError:
                    return -1

            if metric == "pli":
                idx = col_idx("pLI")
            elif metric == "loeuf":
                idx = col_idx("oe_lof_upper")
            else:  # inverse_loeuf
                idx = col_idx("oe_lof_upper")

            for g, gi in ctx.gene_index.items():
                vals = genes_tbl.get(g)
                if vals is None or idx < 0 or idx >= len(vals):
                    continue
                v = vals[idx]
                if v is None:
                    continue
                try:
                    v = float(v)
                except (TypeError, ValueError):
                    continue
                if not np.isfinite(v):
                    continue

                # Skip unreliable genes (flagged) for LOEUF-based metrics.
                fl = flags.get(g, "")
                unreliable = isinstance(fl, str) and ("lof_too_many" in fl or "no_exp_lof" in fl)

                if metric == "pli":
                    scores[gi] = v
                elif metric == "loeuf":
                    scores[gi] = -v  # lower LOEUF = more essential
                else:  # inverse_loeuf
                    if v <= 0:
                        scores[gi] = 10.0
                    elif unreliable:
                        scores[gi] = 1.0
                    else:
                        scores[gi] = 1.0 / max(v, 1e-3)

        cache[key] = scores
        return scores

    def compute(self, ctx, perts, params):
        base = ctx.feature("target_response_similarity_to_mean_e110", perts)
        base = np.asarray(base, dtype=float)
        if base.ndim == 3:
            base = base[:, :, 0]
        elif base.ndim == 1:
            base = base.reshape(len(perts), ctx.n_genes)

        ess = self._essentiality(ctx, params)
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if tgt_idx:
                w = float(np.mean(ess[np.asarray(tgt_idx, dtype=int)]))
            else:
                w = 1.0
            out[i, :, 0] = base[i] * w

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
