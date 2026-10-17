import numpy as np
from genemila.features.api import Feature, register


@register
class RandomProjectionTargetAnnotationE750(Feature):
    name = "random_projection_target_annotation_e750"
    version = 1
    description = ("Random projection of the target gene's complete gene_annotation vector "
                   "(including amino acid fractions) into a lower-dimensional space.")
    rationale = ("High-dimensional random projections can act as universal approximators; "
                 "projecting the target's full annotation captures nonlinear properties.")
    inputs = ["knowledge", "target_genes"]
    params = {"proj_dim": 10, "seed": 750}
    dim = 1

    def _build_annotation_matrix(self, ctx, genes_order):
        """Build a (n_genes, n_features) annotation matrix aligned to genes_order.

        Missing values are imputed with the column mean (or 0 if all missing).
        """
        cache = ctx.cache
        key = ("rpta_e750", "ann_matrix")
        if key in cache:
            mat, cols = cache[key]
            # reindex if needed
            if list(genes_order) == list(cache.get(("rpta_e750", "order"), [])):
                return mat, cols
        ann = ctx.knowledge("gene_annotation")
        n = len(genes_order)
        if not ann or "genes" not in ann or "columns" not in ann:
            mat = np.zeros((n, 1), dtype=float)
            cols = ["__none__"]
            cache[key] = (mat, cols)
            cache[("rpta_e750", "order")] = list(genes_order)
            return mat, cols

        cols = list(ann["columns"])
        n_feat = len(cols)
        gene_ann = ann["genes"]
        mat = np.full((n, n_feat), np.nan, dtype=float)
        for i, g in enumerate(genes_order):
            vals = gene_ann.get(g)
            if vals is None:
                continue
            for j in range(n_feat):
                v = vals[j] if j < len(vals) else None
                if v is None:
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv):
                    mat[i, j] = fv
        # impute NaN with column mean
        col_mean = np.nanmean(mat, axis=0)
        col_mean = np.where(np.isfinite(col_mean), col_mean, 0.0)
        inds = np.where(~np.isfinite(mat))
        if len(inds[0]) > 0:
            mat[inds] = np.take(col_mean, inds[1])
        cache[key] = (mat, cols)
        cache[("rpta_e750", "order")] = list(genes_order)
        return mat, cols

    def compute(self, ctx, perts, params):
        proj_dim = int(params.get("proj_dim", 10))
        seed = int(params.get("seed", 750))
        if proj_dim < 1:
            proj_dim = 1

        n_genes = ctx.n_genes
        genes_order = list(ctx.genes)
        ann_mat, cols = self._build_annotation_matrix(ctx, genes_order)
        n_feat = ann_mat.shape[1]

        # standardize annotation features (z-score) for stable projection
        mu = ann_mat.mean(axis=0)
        sd = ann_mat.std(axis=0)
        sd = np.where(sd > 1e-8, sd, 1.0)
        z = (ann_mat - mu) / sd

        # fixed random projection matrix
        rng = np.random.RandomState(seed)
        W = rng.randn(n_feat, proj_dim).astype(float)
        # normalize columns for unit-ish scale
        W /= np.sqrt(n_feat)

        proj = z @ W  # (n_genes, proj_dim)

        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            tgt_genes = ctx.target_genes(p)
            if not tgt_genes:
                continue
            # use first measured target gene
            tvec = None
            for tg in tgt_genes:
                gi = ctx.gene_index.get(tg)
                if gi is not None:
                    tvec = proj[gi]
                    break
            if tvec is None:
                continue
            # scalar summary: sum of the projected vector broadcast to all genes
            val = float(np.sum(tvec))
            if not np.isfinite(val):
                val = 0.0
            out[i, :, 0] = val

        # ensure finite
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
