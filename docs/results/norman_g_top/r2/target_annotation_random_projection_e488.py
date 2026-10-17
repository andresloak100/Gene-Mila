import numpy as np
from genemila.features.api import Feature, register


@register
class TargetAnnotationRandomProjection(Feature):
    name = "target_annotation_random_projection_e488"
    version = 1
    description = "Random projection of mean target-gene annotation vectors to a low-dim feature."
    rationale = ("A low-dimensional random projection summarises high-dimensional target annotation "
                 "without overfitting, capturing latent biological similarity of perturbations.")
    inputs = ["knowledge", "target_genes"]
    params = {"n_components": 5, "seed": 42}
    dim = 5

    # Columns we try to use from gene_annotation, in a fixed order.
    COLS = ["gc_cds", "gc_promoter", "cpg_oe_promoter", "n_transcripts",
            "transcript_length", "protein_length", "n_exons", "gc_utr3"]

    def _build_matrix(self, ctx, params):
        """Return (col_names, matrix (n_genes, n_cols) with NaN->0, projection (n_cols, k))."""
        ann = ctx.knowledge("gene_annotation")
        k = int(params.get("n_components", 5))
        seed = int(params.get("seed", 42))

        n_genes = ctx.n_genes
        cols = []
        mat = None

        if ann is not None:
            columns = ann.get("columns", [])
            genes = ann.get("genes", {}) or {}
            # choose intersection of desired columns and available ones
            use_cols = [c for c in self.COLS if c in columns]
            if use_cols:
                col_idx = [columns.index(c) for c in use_cols]
                mat = np.zeros((n_genes, len(use_cols)), dtype=np.float64)
                for gi, g in enumerate(ctx.genes):
                    vals = genes.get(g)
                    if vals is None:
                        continue
                    for j, ci in enumerate(col_idx):
                        v = vals[ci] if ci < len(vals) else None
                        if v is None:
                            continue
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv):
                            mat[gi, j] = fv
                cols = use_cols

        if mat is None or mat.shape[1] == 0:
            # fallback: use a small deterministic stand-in so feature is still finite
            mat = np.zeros((n_genes, 1), dtype=np.float64)
            cols = ["_const"]

        # Standardise columns (guard against zero variance)
        mean = mat.mean(axis=0)
        std = mat.std(axis=0)
        std[std < 1e-8] = 1.0
        mat = (mat - mean) / std

        rng = np.random.RandomState(seed)
        proj = rng.normal(0.0, 1.0, size=(mat.shape[1], k)) / np.sqrt(max(mat.shape[1], 1))

        return cols, mat, proj

    def compute(self, ctx, perts, params):
        k = int(params.get("n_components", 5))
        if k != self.dim:
            # keep output shape consistent with declared dim
            k = self.dim

        cache = ctx.cache
        key = ("annotation_proj", k, int(params.get("seed", 42)))
        if key in cache:
            cols, mat, proj = cache[key]
        else:
            cols, mat, proj = self._build_matrix(ctx, params)
            cache[key] = (cols, mat, proj)

        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, self.dim), dtype=np.float64)

        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if not t_idx:
                # no measured target: zero projection
                continue
            t_idx = np.asarray(t_idx, dtype=np.int64)
            # mean annotation vector over targets
            mean_vec = mat[t_idx, :].mean(axis=0)  # (n_cols,)
            proj_vec = mean_vec @ proj           # (k,)
            proj_vec = np.nan_to_num(proj_vec, nan=0.0, posinf=0.0, neginf=0.0)
            out[i, :, :] = proj_vec[None, :]

        return out
