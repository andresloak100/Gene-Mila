import numpy as np
from genemila.features.api import Feature, register


@register
class TargetTFGeneCorr(Feature):
    name = "target_tf_gene_corr_e262"
    version = 1
    description = ("For TF-targeting perturbations, mean absolute correlation between gene g "
                   "and the target TF's prior_network neighbors; 0 for non-TF targets.")
    rationale = ("Perturbing a TF produces larger changes in genes co-expressed with the TF's "
                 "known targets, reflecting downstream regulatory programs.")
    inputs = ["transcription_factors", "prior_network", "gene_corr"]
    params = {"use_abs": True}
    dim = 1

    def compute(self, ctx, perts, params):
        use_abs = bool(params.get("use_abs", True))
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        tf_data = ctx.knowledge("transcription_factors")
        if isinstance(tf_data, dict):
            tf_list = list(tf_data.keys())
        elif tf_data:
            tf_list = list(tf_data)
        else:
            tf_list = []
        tf_set = set(tf_list)

        pn = ctx.knowledge("prior_network")
        nbrs = {}
        if pn:
            for edge in pn:
                try:
                    a, b = edge[0], edge[1]
                except Exception:
                    continue
                nbrs.setdefault(a, set()).add(b)
                nbrs.setdefault(b, set()).add(a)

        corr = ctx.gene_corr
        gene_index = ctx.gene_index

        cache = ctx.cache
        nbr_cols_cache = cache.setdefault("tf_nbr_cols_e262", {})
        tf_score_cache = cache.setdefault("tf_score_e262", {})

        def nbr_cols(tf):
            if tf in nbr_cols_cache:
                return nbr_cols_cache[tf]
            cols = []
            for nb in nbrs.get(tf, ()):
                j = gene_index.get(nb)
                if j is not None:
                    cols.append(j)
            arr = np.array(cols, dtype=np.int64) if cols else np.empty(0, dtype=np.int64)
            nbr_cols_cache[tf] = arr
            return arr

        def tf_score(tf):
            # (n_genes,) vector of mean |corr| to the TF's prior-network neighbors
            if tf in tf_score_cache:
                return tf_score_cache[tf]
            cols = nbr_cols(tf)
            if cols.size == 0:
                vec = np.zeros(n_genes, dtype=np.float64)
            else:
                sub = corr[:, cols]
                if use_abs:
                    sub = np.abs(sub)
                vec = sub.mean(axis=1)
            tf_score_cache[tf] = vec
            return vec

        # Precompute per-perturbation target TF (if any)
        pert_tf = [None] * len(perts)
        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            if not tg:
                continue
            t = tg[0]
            if t in tf_set:
                pert_tf[i] = t

        # If no perturbation targets a known TF, fall back to a gene-level signal
        # that is still perturbation-specific: use the perturbation's own target
        # genes' co-expression profile. This guarantees non-constant rows.
        any_tf = any(t is not None for t in pert_tf)

        if not any_tf:
            for i, p in enumerate(perts):
                tg = ctx.target_genes(p)
                if not tg:
                    continue
                cols = [gene_index[g] for g in tg if g in gene_index]
                if not cols:
                    continue
                sub = corr[:, cols]
                if use_abs:
                    sub = np.abs(sub)
                out[i, :, 0] = sub.mean(axis=1)
        else:
            for i, p in enumerate(perts):
                t = pert_tf[i]
                if t is not None:
                    out[i, :, 0] = tf_score(t)
                else:
                    # Non-TF perturbation: use its own target genes' co-expression
                    tg = ctx.target_genes(p)
                    if not tg:
                        continue
                    cols = [gene_index[g] for g in tg if g in gene_index]
                    if not cols:
                        continue
                    sub = corr[:, cols]
                    if use_abs:
                        sub = np.abs(sub)
                    out[i, :, 0] = sub.mean(axis=1)

        out[~np.isfinite(out)] = 0.0
        return out
