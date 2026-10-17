import numpy as np
from genemila.features.api import Feature, register


@register
class TargetTfbsCountE204(Feature):
    name = "target_tfbs_count_e204"
    version = 1
    description = ("Average number of predicted transcription factor binding sites in the "
                   "promoter region of each perturbation's target genes, broadcast to all genes.")
    rationale = ("Promoter complexity / TFBS density may proxy how strongly a target can be "
                 "activated by CRISPRa and thus how large its downstream response is.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def _promoter_score(self, ctx):
        cache = ctx.cache
        if "tfbs_score" in cache:
            return cache["tfbs_score"]

        n = ctx.n_genes
        score = np.zeros(n, dtype=float)
        ann = ctx.knowledge("gene_annotation")
        if ann is None:
            cache["tfbs_score"] = score
            return score

        genes = ann.get("genes", {}) or {}
        cols = ann.get("columns", []) or []
        col_idx = {c: i for i, c in enumerate(cols)}

        # Preferred proxies for promoter TFBS density, in order of usefulness.
        # n_upstream_atg ~ number of ATGs upstream (proxy for promoter complexity),
        # n_tss_within_100kb ~ local promoter/TSS density, gc_promoter ~ promoter GC.
        use_keys = []
        for k in ("n_upstream_atg", "n_tss_within_100kb", "gc_promoter"):
            if k in col_idx:
                use_keys.append(k)

        if not use_keys:
            cache["tfbs_score"] = score
            return score

        raw = np.full((n, len(use_keys)), np.nan, dtype=float)
        for g, gi in ctx.gene_index.items():
            vals = genes.get(g)
            if vals is None:
                continue
            for j, k in enumerate(use_keys):
                try:
                    v = vals[col_idx[k]]
                except (IndexError, TypeError):
                    v = None
                if v is None:
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv):
                    raw[gi, j] = fv

        # Standardise each proxy across genes (robust, finite-only) and average.
        parts = []
        for j in range(raw.shape[1]):
            col = raw[:, j]
            mask = np.isfinite(col)
            if not mask.any():
                continue
            vals = col[mask]
            mu = vals.mean()
            sd = vals.std()
            if sd <= 0 or not np.isfinite(sd):
                z = np.zeros(n, dtype=float)
            else:
                z = np.where(mask, (col - mu) / sd, 0.0)
            parts.append(z)

        if parts:
            score = np.mean(np.vstack(parts), axis=0)

        # Shift to non-negative so it behaves like a count-like score.
        if score.size:
            mn = score.min()
            if mn < 0:
                score = score - mn

        cache["tfbs_score"] = score
        return score

    def compute(self, ctx, perts, params):
        score = self._promoter_score(ctx)
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            idxs = ctx.target_indices(p)
            if len(idxs) == 0:
                val = 0.0
            else:
                val = float(np.mean(score[np.asarray(idxs, dtype=int)]))
            if not np.isfinite(val):
                val = 0.0
            out[i, :, 0] = val
        return out
