import numpy as np
from genemila.features.api import Feature, register


@register
class AnnotationProjectionSimilarityV2(Feature):
    name = "annotation_projection_similarity_v2_e197"
    version = 1
    description = "Cosine similarity between multiple random projections of gene annotation vectors for target and gene g, averaged over top-k projections."
    rationale = "Multiple random projections of high-dimensional annotation vectors capture complementary gene-gene similarity signal beyond a single projection."
    inputs = ["knowledge"]
    params = {"n_projections": 5, "top_k": 3, "seed": 197}
    dim = 1

    def _build_annotation_matrix(self, ctx):
        cache = ctx.cache
        key = "_apsv2_ann"
        if key in cache:
            return cache[key]

        ga = ctx.knowledge("gene_annotation")
        pa = ctx.knowledge("protein_annotation")

        n = ctx.n_genes
        feats = []

        # gene_annotation numeric columns
        if ga is not None and isinstance(ga, dict):
            cols = ga.get("columns", []) or []
            genes = ga.get("genes", {}) or {}
            for j, cname in enumerate(cols):
                vec = np.full(n, np.nan, dtype=np.float64)
                for i, g in enumerate(ctx.genes):
                    v = genes.get(g)
                    if v is None:
                        continue
                    try:
                        x = v[j]
                    except Exception:
                        continue
                    if x is None:
                        continue
                    try:
                        xf = float(x)
                    except Exception:
                        continue
                    if np.isfinite(xf):
                        vec[i] = xf
                feats.append(vec)

        # protein_annotation numeric columns
        if pa is not None and isinstance(pa, dict):
            cols = pa.get("columns", []) or []
            genes = pa.get("genes", {}) or {}
            for j, cname in enumerate(cols):
                vec = np.full(n, np.nan, dtype=np.float64)
                for i, g in enumerate(ctx.genes):
                    v = genes.get(g)
                    if v is None:
                        continue
                    try:
                        x = v[j]
                    except Exception:
                        continue
                    if x is None:
                        continue
                    try:
                        xf = float(x)
                    except Exception:
                        continue
                    if np.isfinite(xf):
                        vec[i] = xf
                feats.append(vec)

        if not feats:
            mat = np.zeros((n, 1), dtype=np.float64)
        else:
            mat = np.stack(feats, axis=1)

        # handle NaNs: column means, then zero
        col_mean = np.nanmean(mat, axis=0)
        col_mean = np.where(np.isfinite(col_mean), col_mean, 0.0)
        inds = np.where(~np.isfinite(mat))
        if inds[0].size > 0:
            mat[inds] = np.take(col_mean, inds[1])

        # z-score columns
        mu = mat.mean(axis=0)
        sd = mat.std(axis=0)
        sd = np.where(sd > 1e-8, sd, 1.0)
        mat = (mat - mu) / sd

        cache[key] = mat
        return mat

    def compute(self, ctx, perts, params):
        n_proj = int(params.get("n_projections", 5))
        top_k = int(params.get("top_k", 3))
        seed = int(params.get("seed", 197))
        if n_proj < 1:
            n_proj = 1
        if top_k < 1:
            top_k = 1
        if top_k > n_proj:
            top_k = n_proj

        ann = self._build_annotation_matrix(ctx)
        n, d = ann.shape

        cache = ctx.cache
        pkey = "_apsv2_proj"
        if pkey in cache and cache[pkey].get("shape") == (n_proj, d):
            proj = cache[pkey]["proj"]
            proj_norm = cache[pkey]["proj_norm"]
        else:
            rng = np.random.default_rng(seed)
            proj = rng.standard_normal((n_proj, d)).astype(np.float64)
            # project all genes: (n_proj, n)
            projected = proj @ ann.T  # (n_proj, n)
            pn = np.linalg.norm(projected, axis=0)
            pn = np.where(pn > 1e-12, pn, 1.0)
            proj_norm = projected / pn[None, :]  # unit-normalised per gene per projection
            cache[pkey] = {"proj": proj, "proj_norm": proj_norm, "shape": (n_proj, d)}

        out = np.zeros((len(perts), n, 1), dtype=np.float64)

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            # average annotation vectors of targets
            tgt_vec = ann[list(tgt_idx), :].mean(axis=0)
            # project target
            tgt_proj = proj @ tgt_vec  # (n_proj,)
            tn = np.linalg.norm(tgt_proj)
            if tn <= 1e-12:
                continue
            tgt_unit = tgt_proj / tn
            # cosine similarity per projection for all genes: (n_proj, n)
            sims = tgt_unit[:, None] * proj_norm  # since both unit
            # top-k across projections per gene
            if top_k >= n_proj:
                topmean = sims.mean(axis=0)
            else:
                part = np.partition(sims, n_proj - top_k, axis=0)[-top_k:, :]
                topmean = part.mean(axis=0)
            out[i, :, 0] = topmean

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
