import numpy as np
from genemila.features.api import Feature, register


@register
class AnnotationProjectionXResponseEntropy(Feature):
    name = "annotation_projection_x_response_entropy_e471"
    version = 1
    description = ("Product of a random projection of standardized gene annotation "
                   "with per-gene response entropy, for each (p,g).")
    rationale = ("Random projections of annotation capture gene-specific regulatory "
                 "potential; interacting with response entropy reveals context-dependent "
                 "effects of that potential.")
    inputs = ["gene_annotation", "response_entropy_e89"]
    params = {"n_components": 20, "seed": 471}
    dim = 1

    def _annotation_matrix(self, ctx, params):
        """Build (n_genes, n_annot) standardized annotation matrix from prior knowledge."""
        key = ("annotation_matrix_e471", params.get("seed", 471))
        if key in ctx.cache:
            return ctx.cache[key]

        ann = ctx.knowledge("gene_annotation")
        n_genes = ctx.n_genes
        if ann is None:
            mat = np.zeros((n_genes, 1), dtype=float)
            ctx.cache[key] = mat
            return mat

        cols = ann.get("columns", [])
        genes = ann.get("genes", {})
        n_cols = len(cols)
        mat = np.full((n_genes, n_cols), np.nan, dtype=float)
        for gi, g in enumerate(ctx.genes):
            vals = genes.get(g)
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

        # Standardize columns; fill missing with column mean (0 after standardize).
        col_mean = np.nanmean(mat, axis=0)
        col_mean = np.where(np.isfinite(col_mean), col_mean, 0.0)
        # replace nan with mean
        inds = np.where(np.isnan(mat))
        if inds[0].size > 0:
            mat[inds] = np.take(col_mean, inds[1])
        col_std = mat.std(axis=0)
        col_std = np.where(col_std > 1e-12, col_std, 1.0)
        mat = (mat - col_mean) / col_std
        mat = np.nan_to_num(mat, nan=0.0, posinf=0.0, neginf=0.0)

        ctx.cache[key] = mat
        return mat

    def compute(self, ctx, perts, params):
        n = len(perts)
        n_genes = ctx.n_genes
        n_comp = int(params.get("n_components", 20))
        seed = int(params.get("seed", 471))

        annot = self._annotation_matrix(ctx, params)  # (n_genes, n_annot)
        n_annot = annot.shape[1]

        # Random projection matrix (n_annot, n_comp), fixed seed.
        rng = np.random.default_rng(seed)
        proj = rng.standard_normal((n_annot, n_comp)) / np.sqrt(max(n_annot, 1))
        gene_proj = annot @ proj  # (n_genes, n_comp)

        # Response entropy per gene, shape (n_genes,).
        ent = ctx.feature("response_entropy_e89", perts, None)
        ent = np.asarray(ent, dtype=float)
        if ent.ndim == 3:
            ent = ent[:, :, 0]
        if ent.shape[0] != n:
            # fallback: broadcast if single row
            if ent.shape[0] == 1:
                ent = np.repeat(ent, n, axis=0)
            else:
                ent = np.resize(ent, (n, n_genes))
        ent = np.nan_to_num(ent, nan=0.0, posinf=0.0, neginf=0.0)

        # Sum of component products: (n, n_genes)
        # gene_proj: (n_genes, n_comp); ent: (n, n_genes)
        out = np.einsum("gc,pg->pg", gene_proj, ent) / np.sqrt(max(n_comp, 1))
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out[:, :, None]
