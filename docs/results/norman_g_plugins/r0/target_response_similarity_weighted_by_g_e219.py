import numpy as np
from genemila.features.api import Feature, register


@register
class TargetResponseSimilarityWeightedByGeneE219(Feature):
    name = "target_response_similarity_weighted_by_g_e219"
    version = 1
    description = ("For gene g and perturbation p, max over target genes t of "
                   "similarity(response_g, response_t) / (1 + distance(g,t)/scale), "
                   "where distance is absolute TSS distance in bp.")
    rationale = ("CRISPRa perturbations can affect neighboring genes; response similarity "
                 "may be stronger for genes close on the chromosome, so weighting by inverse "
                 "genomic distance emphasizes regulatory-sharing neighbors.")
    inputs = ["train_delta", "knowledge"]
    params = {"aggregation": "max", "distance_scale": 100000}
    dim = 1

    def _get_tss(self, ctx):
        cache = ctx.cache
        key = "_e219_tss"
        if key in cache:
            return cache[key]
        tss = {}
        loci = None
        for name in ("gene_annotation",):
            try:
                k = ctx.knowledge(name)
            except Exception:
                k = None
            if isinstance(k, dict) and "loci" in k:
                loci = k["loci"]
                break
        if isinstance(loci, dict):
            for g, v in loci.items():
                try:
                    tss[g] = float(v[1])
                except Exception:
                    continue
        cache[key] = tss
        return tss

    def compute(self, ctx, perts, params):
        agg = params.get("aggregation", "max")
        scale = float(params.get("distance_scale", 100000))
        if not np.isfinite(scale) or scale <= 0:
            scale = 100000.0

        n_genes = ctx.n_genes
        n_perts = len(perts)
        out = np.zeros((n_perts, n_genes, 1), dtype=float)

        tss = self._get_tss(ctx)
        gene_index = ctx.gene_index
        genes = ctx.genes

        # Precompute per-gene TSS array aligned to gene columns (nan if unknown)
        gene_tss = np.full(n_genes, np.nan, dtype=float)
        for g, idx in gene_index.items():
            if g in tss:
                gene_tss[idx] = tss[g]

        # Precompute single-gene response vectors for all train perturbations
        # We need response vectors of target genes (single-gene perturbations).
        # Build a map from gene -> delta vector using train_delta with exclude=p
        # (leakage safe: recompute per p, but cache per exclude set).
        cache = ctx.cache

        def get_train_deltas(exclude):
            ck = ("_e219_td", exclude)
            if ck in cache:
                return cache[ck]
            ids, d = ctx.train_delta(exclude=exclude)
            # map gene -> row index
            gmap = {}
            for j, pid in enumerate(ids):
                gmap[pid] = j
            cache[ck] = (ids, d, gmap)
            return cache[ck]

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue
            target_idx = [gene_index[t] for t in targets if t in gene_index]
            if not target_idx:
                continue

            ids, d, gmap = get_train_deltas(p)
            if d.shape[0] == 0:
                continue

            # For each target t, get its single-gene response vector (if available)
            # similarity(response_g, response_t) = Pearson correlation across control cells?
            # We use correlation of response vectors across genes -> but response vector is per gene.
            # Interpret similarity as correlation between response profiles across training perts?
            # Simpler: use correlation of gene g's response with target t's response across perts.
            # However "response_g" here: single-gene response vector of gene g (across perts).
            # We have control data; use gene_corr as similarity proxy? The hint says
            # "similarity(response_g, response_t)". Given other features use correlations of
            # single-gene response vectors. We'll compute correlation between gene g's
            # single-gene response vector (across training perts) and target t's.
            # But we only need for this p: use response vectors from train deltas.
            # Build response matrix: rows = train perts, cols = genes -> that's d.
            # gene g's response vector = d[:, g]; target t's = d[:, t].
            # Correlate.
            # However for target t, its "response" should be the single-gene response of t.
            # We have d rows for each train pert. For single-gene pert t, its delta is response_t.
            # But we need per-gene response across perts for gene g. Use d[:, g].

            # Precompute standardized columns for correlation
            # Only compute for target columns and all g.
            # To be efficient: compute correlation of each target column with all gene columns.
            # d shape (n_train, n_genes). Standardize columns.
            n = d.shape[0]
            if n < 2:
                continue
            mu = d.mean(axis=0)
            sd = d.std(axis=0)
            sd_safe = np.where(sd > 1e-12, sd, 1.0)
            dz = (d - mu) / sd_safe

            # For each target t, corr with all genes = dz[:, t] @ dz / n
            # (since standardized, mean 0, var 1)
            best = np.full(n_genes, -np.inf, dtype=float)
            any_valid = False
            for t_idx in target_idx:
                if sd[t_idx] <= 1e-12:
                    continue
                corr = (dz[:, t_idx] @ dz) / n  # shape (n_genes,)
                # distance weighting
                tg = gene_tss[t_idx]
                if np.isfinite(tg):
                    dist = np.abs(gene_tss - tg)
                    dist = np.where(np.isfinite(dist), dist, np.inf)
                    w = 1.0 / (1.0 + dist / scale)
                else:
                    w = np.ones(n_genes, dtype=float)
                weighted = corr * w
                # only consider genes with finite tss? keep all
                weighted = np.where(np.isfinite(weighted), weighted, -np.inf)
                if agg == "mean":
                    # accumulate
                    pass
                best = np.maximum(best, weighted)
                any_valid = True

            if not any_valid:
                continue

            if agg == "mean":
                # recompute as mean over targets
                acc = np.zeros(n_genes, dtype=float)
                cnt = np.zeros(n_genes, dtype=float)
                for t_idx in target_idx:
                    if sd[t_idx] <= 1e-12:
                        continue
                    corr = (dz[:, t_idx] @ dz) / n
                    tg = gene_tss[t_idx]
                    if np.isfinite(tg):
                        dist = np.abs(gene_tss - tg)
                        dist = np.where(np.isfinite(dist), dist, np.inf)
                        w = 1.0 / (1.0 + dist / scale)
                    else:
                        w = np.ones(n_genes, dtype=float)
                    weighted = corr * w
                    weighted = np.where(np.isfinite(weighted), weighted, 0.0)
                    acc += weighted
                    cnt += 1.0
                denom = np.where(cnt > 0, cnt, 1.0)
                vals = acc / denom
                vals = np.where(np.isfinite(vals), vals, 0.0)
                out[i, :, 0] = vals
            else:
                vals = np.where(np.isfinite(best), best, 0.0)
                out[i, :, 0] = vals

        out = np.where(np.isfinite(out), out, 0.0)
        return out
