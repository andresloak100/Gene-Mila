import numpy as np
from genemila.features.api import Feature, register


@register
class RandomProjectionTargetAnnotationE737(Feature):
    name = "random_projection_target_annotation_e737"
    version = 1
    description = "Fixed random projection of the target gene's gene_annotation vector (all numeric columns) to 5 dimensions."
    rationale = "Random projections of high-dimensional features can capture latent structure; target annotation may contain hidden signals not captured by selected features."
    inputs = ["knowledge"]
    params = {"n_components": 5, "seed": 42}
    dim = 5

    def compute(self, ctx, perts, params):
        n_comp = int(params.get("n_components", 5))
        seed = int(params.get("seed", 42))

        anno = ctx.knowledge("gene_annotation")
        out = np.zeros((len(perts), ctx.n_genes, n_comp))

        if anno is None or "genes" not in anno or "columns" not in anno:
            return out

        genes_tbl = anno["genes"]
        columns = anno["columns"]
        # Identify numeric columns (skip aa_* which may be null, but keep numeric ones)
        # We use all columns; parse each value to float, treating null as nan.
        n_feat = len(columns)

        # Build matrix over genes: rows = genes present, cols = features
        gene_names = list(genes_tbl.keys())
        if len(gene_names) == 0:
            return out

        mat = np.full((len(gene_names), n_feat), np.nan, dtype=np.float64)
        for gi, g in enumerate(gene_names):
            vals = genes_tbl[g]
            for ci in range(n_feat):
                if ci >= len(vals):
                    continue
                v = vals[ci]
                if v is None:
                    continue
                try:
                    mat[gi, ci] = float(v)
                except (TypeError, ValueError):
                    mat[gi, ci] = np.nan

        # Column means/std ignoring nan
        col_mean = np.nanmean(mat, axis=0)
        col_std = np.nanstd(mat, axis=0)
        col_mean = np.where(np.isfinite(col_mean), col_mean, 0.0)
        col_std = np.where(np.isfinite(col_std) & (col_std > 0), col_std, 1.0)

        # Standardize
        mat_std = (mat - col_mean) / col_std
        # Replace remaining nan with 0
        mat_std = np.where(np.isfinite(mat_std), mat_std, 0.0)

        # Fixed random projection matrix
        rng = np.random.RandomState(seed)
        proj = rng.normal(0.0, 1.0, size=(n_feat, n_comp))

        # Project each gene row
        projected = mat_std @ proj  # (n_genes_in_anno, n_comp)

        name_to_row = {g: i for i, g in enumerate(gene_names)}

        # For each perturbation, get target gene(s) and project
        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            if not tgenes:
                continue
            vecs = []
            for tg in tgenes:
                if tg in name_to_row:
                    vecs.append(projected[name_to_row[tg]])
            if not vecs:
                continue
            vec = np.mean(np.stack(vecs, axis=0), axis=0)
            out[i, :, :] = vec[np.newaxis, :]

        # Ensure finite
        out = np.where(np.isfinite(out), out, 0.0)
        return out
