import numpy as np
from genemila.features.api import Feature, register


@register
class LofWeightedTargetResponseSimilarity(Feature):
    name = "lof_weighted_target_response_similarity_e201"
    version = 1
    description = (
        "For each gene g and perturbation p, weighted average of g's similarity to "
        "each target gene t's single-gene response, weighted by LoF constraint of t."
    )
    rationale = (
        "LoF-intolerant genes may have stronger downstream effects when perturbed, "
        "so weighting target similarity by constraint could prioritize informative targets."
    )
    inputs = ["control_cells", "train_delta", "knowledge"]
    params = {
        "weight_type": "inverse_loeuf",
    }
    dim = 1

    def _get_weights(self, ctx, params):
        key = ("weights", params.get("weight_type", "inverse_loeuf"))
        if key in ctx.cache:
            return ctx.cache[key]
        weight_type = params.get("weight_type", "inverse_loeuf")
        weights = np.ones(ctx.n_genes, dtype=np.float64)
        kn = ctx.knowledge("gene_constraint")
        if kn is not None:
            cols = kn.get("columns", [])
            genes = kn.get("genes", {})
            try:
                i_loeuf = cols.index("oe_lof_upper")
            except ValueError:
                i_loeuf = None
            try:
                i_pli = cols.index("pLI")
            except ValueError:
                i_pli = None
            eps = 1e-6
            for gi, g in enumerate(ctx.genes):
                vals = genes.get(g)
                if vals is None:
                    continue
                try:
                    if weight_type == "pli" and i_pli is not None:
                        v = vals[i_pli]
                        if v is not None:
                            weights[gi] = float(v)
                    elif weight_type == "inverse_loeuf" and i_loeuf is not None:
                        v = vals[i_loeuf]
                        if v is not None:
                            weights[gi] = 1.0 / (float(v) + eps)
                    elif weight_type == "inverse_pli" and i_pli is not None:
                        v = vals[i_pli]
                        if v is not None:
                            weights[gi] = 1.0 / (float(v) + eps)
                except (TypeError, ValueError, IndexError):
                    continue
        weights = np.where(np.isfinite(weights) & (weights > 0), weights, 1.0)
        ctx.cache[key] = weights
        return weights

    def _get_target_vectors(self, ctx, p):
        cache = ctx.cache.setdefault("loo_perts", {})
        if p in cache:
            return cache[p]
        targets = ctx.target_genes(p)
        train_ids, deltas = ctx.train_delta(exclude=p)
        id_to_row = {pid: i for i, pid in enumerate(train_ids)}
        vecs = []
        for t in targets:
            if t in id_to_row:
                vecs.append((t, deltas[id_to_row[t]]))
        cache[p] = vecs
        return vecs

    def compute(self, ctx, perts, params):
        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1), dtype=np.float64)
        weights = self._get_weights(ctx, params)
        n_genes = ctx.n_genes

        # Control-cell correlation matrix proxy: use gene_corr directly.
        gene_corr = ctx.gene_corr
        if gene_corr is None:
            gene_corr = np.eye(n_genes, dtype=np.float64)

        for i, p in enumerate(perts):
            vecs = self._get_target_vectors(ctx, p)
            if not vecs:
                continue
            sims = np.zeros(n_genes, dtype=np.float64)
            wsum = 0.0
            for t, resp in vecs:
                ti = ctx.gene_index.get(t)
                if ti is None:
                    continue
                w = weights[ti]
                if not np.isfinite(w) or w <= 0:
                    continue
                r = np.asarray(resp, dtype=np.float64).ravel()
                if r.shape[0] != n_genes:
                    # align by min length defensively
                    m = min(r.shape[0], n_genes)
                    rv = np.zeros(n_genes, dtype=np.float64)
                    rv[:m] = r[:m]
                    r = rv
                rmu = r.mean()
                rsd = r.std()
                if rsd <= 1e-12:
                    continue
                rz = (r - rmu) / rsd
                rzn = np.sqrt(float(rz @ rz))
                if rzn <= 1e-12:
                    continue
                # similarity of each gene g to target response vector rz
                dots = gene_corr.T @ rz  # (n_genes,)
                denom = np.sqrt(np.clip(np.diag(gene_corr), 1e-12, None)) * rzn
                corr = dots / denom
                corr = np.where(np.isfinite(corr), corr, 0.0)
                sims += w * corr
                wsum += w
            if wsum > 0:
                out[i, :, 0] = sims / wsum

        out = np.where(np.isfinite(out), out, 0.0)
        return out
