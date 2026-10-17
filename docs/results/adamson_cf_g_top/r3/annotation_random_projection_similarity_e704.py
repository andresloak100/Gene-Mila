import numpy as np
from genemila.features.api import Feature, register


@register
class AnnotationRandomProjectionSimilarity(Feature):
    name = "annotation_random_projection_similarity_e704"
    version = 1
    description = "Cosine similarity between random projections of target and gene annotation vectors."
    rationale = (
        "Gene annotation features capture latent biological properties; a low-dimensional "
        "random projection yields compact signatures whose cosine similarity reflects "
        "annotation-level similarity between the perturbation target and each gene."
    )
    inputs = ["knowledge:gene_annotation", "target_genes"]
    params = {"projection_dim": 20, "random_seed": 42}
    dim = 1

    def _build_matrix(self, ctx, params):
        cache = ctx.cache
        key = ("arps_e704", params.get("projection_dim", 20), params.get("random_seed", 42))
        if key in cache:
            return cache[key]

        ann = ctx.knowledge("gene_annotation")
        n_genes = ctx.n_genes
        # Collect numeric annotation columns per gene.
        mat = np.zeros((n_genes, 0), dtype=np.float64)
        if ann is not None and isinstance(ann, dict):
            genes_map = ann.get("genes", {}) or {}
            columns = ann.get("columns", []) or []
            n_cols = len(columns)
            if n_cols == 0 and genes_map:
                # infer width
                for v in genes_map.values():
                    if isinstance(v, (list, tuple)):
                        n_cols = len(v)
                        break
            if n_cols > 0:
                mat = np.full((n_genes, n_cols), np.nan, dtype=np.float64)
                for gi, gname in enumerate(ctx.genes):
                    vals = genes_map.get(gname)
                    if vals is None:
                        continue
                    arr = np.asarray(vals, dtype=object)
                    m = min(n_cols, arr.shape[0])
                    for j in range(m):
                        v = arr[j]
                        if v is None:
                            continue
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv):
                            mat[gi, j] = fv

        # Handle NaN: column-mean imputation, then zero if all-NaN.
        if mat.shape[1] > 0:
            col_means = np.nanmean(np.where(np.isfinite(mat), mat, np.nan), axis=0)
            col_means = np.where(np.isfinite(col_means), col_means, 0.0)
            inds = np.where(~np.isfinite(mat))
            if inds[0].size > 0:
                mat[inds] = np.take(col_means, inds[1])
            # Standardise columns (guard zero std).
            mu = mat.mean(axis=0)
            sd = mat.std(axis=0)
            sd = np.where(sd > 1e-12, sd, 1.0)
            mat = (mat - mu) / sd
        else:
            mat = np.zeros((n_genes, 1), dtype=np.float64)

        seed = int(params.get("random_seed", 42))
        pdim = int(params.get("projection_dim", 20))
        pdim = max(1, pdim)
        rng = np.random.RandomState(seed)
        proj = rng.normal(0.0, 1.0, size=(mat.shape[1], pdim)) / np.sqrt(max(1, mat.shape[1]))
        projected = mat @ proj  # (n_genes, pdim)
        norms = np.linalg.norm(projected, axis=1)
        norms = np.where(norms > 1e-12, norms, 1.0)
        unit = projected / norms[:, None]

        cache[key] = unit
        return unit

    def compute(self, ctx, perts, params):
        unit = self._build_matrix(ctx, params)
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=np.float64)
        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            tgt_vec = unit[tgt_idx].mean(axis=0)
            n = np.linalg.norm(tgt_vec)
            if n > 1e-12:
                tgt_vec = tgt_vec / n
            else:
                continue
            sims = unit @ tgt_vec
            out[i, :, 0] = sims
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
