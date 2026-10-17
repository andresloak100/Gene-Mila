import numpy as np
from genemila.features.api import Feature, register


@register
class EssentialityWeightedResponseSimilarityE379(Feature):
    name = "essentiality_weighted_response_similarit_e379"
    version = 1
    description = (
        "Leave-one-out weighted average of gene g's response similarity to training "
        "perturbations q, weighted by the essentiality score of q's target gene(s)."
    )
    rationale = (
        "Essential genes may elicit stronger or more consistent transcriptional "
        "responses; weighting similarity by essentiality emphasizes informative "
        "training perturbations."
    )
    inputs = ["train_delta", "gene_corr", "control_cells"]
    params = {"essentiality_metric": "loeuf_inverse"}
    dim = 1

    def _essentiality(self, ctx, metric):
        cache = ctx.cache
        key = "ess_scores_" + metric
        if key in cache:
            return cache[key]

        scores = np.ones(ctx.n_genes, dtype=np.float64)

        kc = ctx.knowledge("gene_constraint")
        if kc is not None and isinstance(kc, dict) and "genes" in kc:
            cols = kc.get("columns", [])
            genes_tbl = kc["genes"]
            # find column index for loeuf / pli
            col_idx = None
            if metric == "loeuf_inverse":
                for cand in ["oe_lof_upper", "loeuf", "LOEUF"]:
                    if cand in cols:
                        col_idx = cols.index(cand)
                        break
            elif metric == "pli":
                for cand in ["pLI", "pli"]:
                    if cand in cols:
                        col_idx = cols.index(cand)
                        break
            if col_idx is None:
                # fall back to first column if present
                if len(cols) > 0:
                    col_idx = 0

            if col_idx is not None:
                for g, gi in ctx.gene_index.items():
                    if g in genes_tbl:
                        vals = genes_tbl[g]
                        try:
                            v = vals[col_idx]
                        except Exception:
                            continue
                        if v is None:
                            continue
                        try:
                            v = float(v)
                        except Exception:
                            continue
                        if not np.isfinite(v):
                            continue
                        if metric == "loeuf_inverse":
                            # low LOEUF = essential -> inverse score
                            s = 1.0 / (v + 1e-3)
                        else:
                            s = v
                        scores[gi] = s

        # normalise to mean 1 to keep scale stable
        m = scores.mean()
        if m > 0 and np.isfinite(m):
            scores = scores / m
        scores = np.where(np.isfinite(scores), scores, 1.0)
        scores = np.clip(scores, 1e-3, 1e3)
        cache[key] = scores
        return scores

    def _pert_target_score(self, ctx, p, scores):
        idx = ctx.target_indices(p)
        if not idx:
            return 1.0
        vals = scores[np.asarray(idx, dtype=int)]
        if vals.size == 0:
            return 1.0
        return float(np.mean(vals))

    def compute(self, ctx, perts, params):
        metric = params.get("essentiality_metric", "loeuf_inverse")
        scores = self._essentiality(ctx, metric)

        # Precompute per-gene response similarity helper via gene_corr.
        # gene_corr is (n_genes, n_genes) correlation across control cells.
        # For a perturbation q with target set T_q, the "response similarity"
        # of gene g to q is taken as the mean control correlation of g with
        # the target genes of q (a proxy for shared regulatory program).
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=np.float64)

        # Cache per-perturbation similarity vectors
        sim_cache = {}

        def sim_vec(pert):
            if pert in sim_cache:
                return sim_cache[pert]
            idx = ctx.target_indices(pert)
            if not idx:
                v = np.zeros(n_genes, dtype=np.float64)
            else:
                cols = ctx.gene_corr[:, np.asarray(idx, dtype=int)]
                v = cols.mean(axis=1)
            v = np.where(np.isfinite(v), v, 0.0)
            sim_cache[pert] = v
            return v

        for i, p in enumerate(perts):
            train_ids, deltas = ctx.train_delta(exclude=p)
            n = len(train_ids)
            if n == 0:
                continue

            weights = np.empty(n, dtype=np.float64)
            sims = np.empty((n, n_genes), dtype=np.float64)
            for j, q in enumerate(train_ids):
                weights[j] = self._pert_target_score(ctx, q, scores)
                sims[j] = sim_vec(q)

            wsum = weights.sum()
            if wsum <= 0 or not np.isfinite(wsum):
                weights = np.ones(n, dtype=np.float64)
                wsum = float(n)

            w = weights / wsum
            # weighted average of similarity vectors
            avg_sim = np.tensordot(w, sims, axes=(0, 0))
            avg_sim = np.where(np.isfinite(avg_sim), avg_sim, 0.0)
            out[i, :, 0] = avg_sim

        return out
