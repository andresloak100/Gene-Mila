import numpy as np
from genemila.features.api import Feature, register


@register
class GenomicDistanceWeightedResponseSimilE581(Feature):
    name = "genomic_distance_weighted_response_simil_e581"
    version = 1
    description = ("For gene g and perturbation p, weighted average of training deltas for genes "
                   "near g, weights inversely proportional to genomic distance from g's TSS.")
    rationale = ("Genes closer in genomic distance to a perturbation target may share regulatory "
                 "context, so a distance-decayed neighbourhood average of training deltas can "
                 "capture local effects.")
    inputs = ["train_delta", "knowledge"]
    params = {"max_distance_kb": 100, "smoothing": 1.0}
    dim = 1

    def _build_neighbour_weights(self, ctx, max_distance_kb, smoothing):
        cache = ctx.cache
        key = "_gdw581_neigh_weights"
        if key in cache:
            return cache[key]

        n = ctx.n_genes
        max_bp = float(max_distance_kb) * 1000.0
        W = np.zeros((n, n), dtype=np.float64)

        ann = ctx.knowledge("gene_annotation")
        loci = None
        if isinstance(ann, dict):
            loci = ann.get("loci")
        if not isinstance(loci, dict):
            # fallback: identity-only weighting
            W[np.arange(n), np.arange(n)] = 1.0
            cache[key] = W
            return W

        chroms = [None] * n
        tss = [np.nan] * n
        for g, col in ctx.gene_index.items():
            loc = loci.get(g)
            if not loc or len(loc) < 2:
                continue
            try:
                chroms[col] = loc[0]
                tss[col] = float(loc[1])
            except (TypeError, ValueError):
                continue

        # group by chromosome, compute pairwise distances
        chrom_arr = np.array([c if c is not None else "" for c in chroms], dtype=object)
        tss_arr = np.array(tss, dtype=np.float64)

        for c in set(chrom_arr):
            if c == "":
                continue
            idx = np.where(chrom_arr == c)[0]
            if idx.size == 0:
                continue
            t = tss_arr[idx]
            valid = np.isfinite(t)
            idx = idx[valid]
            t = t[valid]
            if idx.size == 0:
                continue
            d = np.abs(t[:, None] - t[None, :])
            w = 1.0 / (d + float(smoothing))
            w[d > max_bp] = 0.0
            W[np.ix_(idx, idx)] = w

        # ensure self weight is at least 1/smoothing
        diag = np.diag(W).copy()
        self_w = 1.0 / float(smoothing)
        bad = diag <= 0
        if bad.any():
            ii = np.where(bad)[0]
            W[ii, ii] = self_w

        cache[key] = W
        return W

    def compute(self, ctx, perts, params):
        max_distance_kb = float(params.get("max_distance_kb", 100))
        smoothing = float(params.get("smoothing", 1.0))

        W = self._build_neighbour_weights(ctx, max_distance_kb, smoothing)
        row_sums = W.sum(axis=1)
        row_sums[row_sums <= 0] = 1.0

        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1), dtype=np.float64)

        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            if d.shape[0] == 0:
                continue
            # mean over training perturbations of (weighted neighbour average of delta)
            # d: (n_train, n_genes)
            # weighted neighbour average per training pert: (W @ d.T) / row_sums
            agg = d.mean(axis=0)  # (n_genes,)
            # apply neighbourhood smoothing to the mean delta
            smoothed = (W @ agg) / row_sums
            out[i, :, 0] = smoothed

        out[~np.isfinite(out)] = 0.0
        return out
