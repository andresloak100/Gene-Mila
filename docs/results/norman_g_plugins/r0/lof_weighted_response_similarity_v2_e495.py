import numpy as np
from genemila.features.api import Feature, register


@register
class LofWeightedResponseSimilarityV2(Feature):
    name = "lof_weighted_response_similarity_v2_e495"
    version = 1
    description = ("For perturbation p and gene g, cosine similarity between g's response vector "
                   "(across training perturbations) and each target's response vector, weighted by "
                   "1/LOEUF of the target and averaged over targets.")
    rationale = ("Perturbations of LoF-intolerant (essential) genes may produce stronger or more "
                 "distinctive downstream effects; weighting target response similarity by inverse "
                 "LOEUF emphasises such targets.")
    inputs = ["train_delta", "knowledge"]
    params = {}
    dim = 1

    def _lof_weights(self, ctx):
        cache = ctx.cache
        key = "_lof_w_495"
        if key in cache:
            return cache[key]
        w = np.zeros(ctx.n_genes, dtype=float)
        kn = ctx.knowledge("gene_constraint")
        if kn is not None:
            cols = kn.get("columns", [])
            genes = kn.get("genes", {})
            try:
                idx = cols.index("oe_lof_upper")
            except ValueError:
                idx = None
            if idx is not None:
                for gi, gname in enumerate(ctx.genes):
                    vals = genes.get(gname)
                    if vals is None:
                        continue
                    try:
                        v = vals[idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        v = float(v)
                    except (TypeError, ValueError):
                        continue
                    if not np.isfinite(v) or v <= 0:
                        continue
                    w[gi] = 1.0 / v
        cache[key] = w
        return w

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        lof_w = self._lof_weights(ctx)

        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            # d: (n_train_perts, n_genes)
            if d.shape[0] == 0:
                continue
            # column norms of d
            norms = np.sqrt(np.sum(d * d, axis=0))
            safe_norms = np.where(norms > 0, norms, 1.0)

            targets = ctx.target_indices(p)
            if not targets:
                continue

            acc = np.zeros(ctx.n_genes, dtype=float)
            wtot = 0.0
            for t in targets:
                w = lof_w[t] if 0 <= t < ctx.n_genes else 0.0
                if w <= 0:
                    continue
                col_t = d[:, t]
                nt = norms[t]
                if nt <= 0:
                    continue
                # cosine similarity of every gene column with column t
                dots = d.T @ col_t  # (n_genes,)
                sims = dots / (safe_norms * nt)
                acc += w * sims
                wtot += w

            if wtot > 0:
                out[i, :, 0] = acc / wtot

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
