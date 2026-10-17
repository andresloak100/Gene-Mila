import numpy as np
from genemila.features.api import Feature, register


@register
class AnnotationRandomProjectionTargetInteraction(Feature):
    name = "annotation_random_projection_target_inte_e379"
    version = 1
    description = (
        "Element-wise product of random projections of gene annotation vectors "
        "for each gene g and the perturbation target gene t, reduced to a scalar."
    )
    rationale = (
        "Random projections of annotation create a rich nonlinear feature space; "
        "interacting the projected target vector with the projected gene vector may "
        "capture target-specific annotation relationships driving response."
    )
    inputs = ["gene_annotation"]
    params = {"projection_dim": 50, "seed": 42}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is None or "genes" not in ann:
            return out

        cols = ann.get("columns", [])
        gene_vals = ann["genes"]
        n_cols = len(cols)

        # Build per-gene annotation matrix over ctx.genes, standardized, NaN->0.
        mat = np.zeros((n_genes, n_cols), dtype=float)
        mask = np.zeros((n_genes, n_cols), dtype=bool)
        for gi, g in enumerate(ctx.genes):
            vals = gene_vals.get(g)
            if vals is None:
                continue
            for ci in range(min(n_cols, len(vals))):
                v = vals[ci]
                if v is None:
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv):
                    mat[gi, ci] = fv
                    mask[gi, ci] = True

        # Standardize per column using observed entries.
        for ci in range(n_cols):
            m = mask[:, ci]
            if m.sum() < 2:
                mat[:, ci] = 0.0
                continue
            col = mat[m, ci]
            mu = col.mean()
            sd = col.std()
            if sd <= 1e-12:
                mat[:, ci] = 0.0
            else:
                mat[:, ci] = (mat[:, ci] - mu) / sd
                mat[~m, ci] = 0.0

        pdim = int(params.get("projection_dim", 50))
        seed = int(params.get("seed", 42))
        pdim = max(1, min(pdim, 512))

        rng = np.random.RandomState(seed)
        R = rng.randn(n_cols, pdim) / np.sqrt(max(1, pdim))

        proj = mat @ R  # (n_genes, pdim)

        # Normalize each projected row (safely) so products are bounded.
        norms = np.linalg.norm(proj, axis=1, keepdims=True)
        norms[norms < 1e-12] = 1.0
        proj_n = proj / norms

        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if not t_idx:
                continue
            t_vec = proj_n[t_idx, :].mean(axis=0)  # (pdim,)
            # Element-wise product then reduce (mean) to a scalar per gene.
            val = (proj_n * t_vec[None, :]).mean(axis=1)
            out[i, :, 0] = val

        out[~np.isfinite(out)] = 0.0
        return out
