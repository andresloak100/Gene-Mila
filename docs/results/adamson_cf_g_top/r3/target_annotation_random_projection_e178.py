import numpy as np
from genemila.features.api import Feature, register


@register
class TargetAnnotationRandomProjectionE178(Feature):
    name = "target_annotation_random_projection_e178"
    version = 1
    description = ("Random projection (Gaussian, seeded) of the standardized numeric "
                   "gene-annotation vector of the perturbation's target gene into k dims.")
    rationale = ("Gene annotation carries many correlated numeric properties; a fixed "
                 "random projection compresses them into k low-dimensional target descriptors "
                 "that can capture nonlinear target effects without overfitting.")
    inputs = ["knowledge:gene_annotation", "target_indices"]
    params = {"k": 5, "seed": 42}
    dim = 5

    def compute(self, ctx, perts, params):
        k = int(params.get("k", 5))
        seed = int(params.get("seed", 42))
        self.dim = k

        out = np.zeros((len(perts), ctx.n_genes, k), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if not ann or "genes" not in ann or "columns" not in ann:
            return out

        columns = list(ann["columns"])
        genes_table = ann["genes"]

        # Build annotation matrix in a stable gene order (ctx.genes).
        n_ann = len(columns)
        A = np.full((ctx.n_genes, n_ann), np.nan, dtype=float)
        for gi, g in enumerate(ctx.genes):
            vals = genes_table.get(g)
            if vals is None:
                continue
            for j in range(min(n_ann, len(vals))):
                v = vals[j]
                if v is None:
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv):
                    A[gi, j] = fv

        # Keep columns with enough finite values; median-fill the rest.
        finite_mask = np.isfinite(A)
        col_counts = finite_mask.sum(axis=0)
        min_count = max(2, int(0.1 * ctx.n_genes))
        keep = col_counts >= min_count
        if not np.any(keep):
            return out
        A = A[:, keep]
        n_ann = A.shape[1]

        # Median-fill missing entries column-wise.
        for j in range(n_ann):
            col = A[:, j]
            m = np.isfinite(col)
            if not np.any(m):
                A[:, j] = 0.0
                continue
            med = float(np.median(col[m]))
            col[~m] = med
            A[:, j] = col

        # Standardize to zero mean unit variance across genes.
        mu = A.mean(axis=0)
        sd = A.std(axis=0)
        sd[sd < 1e-8] = 1.0
        Z = (A - mu) / sd

        # Fixed random projection matrix.
        rng = np.random.RandomState(seed)
        W = rng.standard_normal((n_ann, k)) / np.sqrt(max(n_ann, 1))

        proj = Z.dot(W)  # (n_genes, k)

        # Fill output: same projected vector for every gene column of a perturbation,
        # determined by that perturbation's target gene annotation.
        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                vec = np.zeros(k, dtype=float)
            else:
                vec = proj[tgt_idx[0]]
            if not np.all(np.isfinite(vec)):
                vec = np.where(np.isfinite(vec), vec, 0.0)
            out[i, :, :] = vec[None, :]

        return out
