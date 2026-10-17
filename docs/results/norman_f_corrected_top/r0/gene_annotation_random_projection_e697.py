import numpy as np
from genemila.features.api import Feature, register


@register
class GeneAnnotationRandomProjectionE697(Feature):
    name = "gene_annotation_random_projection_e697"
    version = 1
    description = "Random projection of the full gene annotation vector per gene, averaged over the perturbation's targets, multiplied by additive_response."
    rationale = "A random linear combination of all gene annotation features may capture latent biological signal not captured by individual annotations, and interacting it with additive_response lets the model scale the projection by the expected perturbation effect."
    inputs = ["gene_annotation", "additive_response"]
    params = {"seed": 42}
    dim = 1

    def compute(self, ctx, perts, params):
        seed = int(params.get("seed", 42))
        n_genes = ctx.n_genes

        ann = ctx.knowledge("gene_annotation")
        if ann is None:
            return np.zeros((len(perts), n_genes, 1))

        genes_ann = ann.get("genes", {})
        columns = ann.get("columns", [])
        if not columns:
            return np.zeros((len(perts), n_genes, 1))

        # Build annotation matrix in ctx gene order
        n_cols = len(columns)
        A = np.zeros((n_genes, n_cols), dtype=np.float64)
        present = np.zeros(n_genes, dtype=bool)
        for gi, g in enumerate(ctx.genes):
            vals = genes_ann.get(g)
            if vals is None:
                continue
            row = np.asarray(vals, dtype=np.float64)
            if row.shape[0] != n_cols:
                # pad/truncate defensively
                m = min(row.shape[0], n_cols)
                A[gi, :m] = row[:m]
            else:
                A[gi, :] = row
            present[gi] = True

        # Replace non-finite with column mean (finite values only)
        A[~np.isfinite(A)] = np.nan
        col_mean = np.nanmean(A, axis=0)
        col_mean = np.where(np.isfinite(col_mean), col_mean, 0.0)
        inds = np.where(~np.isfinite(A))
        if inds[0].size:
            A[inds] = np.take(col_mean, inds[1])

        # Fixed random projection vector
        rng = np.random.RandomState(seed)
        w = rng.randn(n_cols)
        w = w / (np.linalg.norm(w) + 1e-12)

        proj = A.dot(w)  # (n_genes,)

        # additive_response from composed feature
        add = ctx.feature("additive_response", perts, params=None)
        add = np.asarray(add, dtype=np.float64)
        if add.ndim == 3:
            add = add[:, :, 0]
        add = np.nan_to_num(add, nan=0.0, posinf=0.0, neginf=0.0)

        out = np.zeros((len(perts), n_genes, 1), dtype=np.float64)
        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if t_idx:
                tproj = proj[t_idx].mean()
            else:
                tproj = 0.0
            out[i, :, 0] = tproj * add[i]

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
