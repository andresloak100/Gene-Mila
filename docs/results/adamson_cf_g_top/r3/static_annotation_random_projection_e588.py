import numpy as np
from genemila.features.api import Feature, register


@register
class StaticAnnotationRandomProjection(Feature):
    name = "static_annotation_random_projection_e588"
    version = 1
    description = ("Random projection of concatenated static per-gene annotation features "
                   "(gene_annotation, gene_constraint, protein_annotation) into a low-dimensional space.")
    rationale = ("Static annotations summarize a gene's structural/functional context; a random "
                 "projection compresses them into a few latent dimensions that may correlate with "
                 "perturbation response magnitude.")
    inputs = ["knowledge"]
    params = {"n_components": 10, "random_state": 42}
    dim = 10

    def compute(self, ctx, perts, params):
        n_comp = int(params.get("n_components", 10))
        seed = int(params.get("random_state", 42))

        cache_key = ("static_ann_proj", n_comp, seed)
        if cache_key in ctx.cache:
            proj = ctx.cache[cache_key]
        else:
            proj = self._build_projection(ctx, n_comp, seed)
            ctx.cache[cache_key] = proj

        n = len(perts)
        out = np.zeros((n, ctx.n_genes, n_comp), dtype=float)
        for i in range(n):
            out[i, :, :] = proj
        return out

    def _build_projection(self, ctx, n_comp, seed):
        n_genes = ctx.n_genes
        rows = []

        ann = ctx.knowledge("gene_annotation")
        con = ctx.knowledge("gene_constraint")
        prot = ctx.knowledge("protein_annotation")

        def _numeric_matrix(knowledge, genes, columns):
            """Build (n_genes, n_cols) numeric matrix from knowledge['genes'] dict."""
            mat = np.full((n_genes, len(columns)), np.nan, dtype=float)
            if knowledge is None:
                return mat
            table = knowledge.get("genes", {}) if isinstance(knowledge, dict) else {}
            for gi, g in enumerate(genes):
                vals = table.get(g)
                if vals is None:
                    continue
                for ci, col in enumerate(columns):
                    try:
                        idx = knowledge.get("columns", []).index(col)
                    except ValueError:
                        idx = ci
                    if idx < len(vals):
                        v = vals[idx]
                        if v is not None:
                            try:
                                mat[gi, ci] = float(v)
                            except (TypeError, ValueError):
                                pass
            return mat

        genes = ctx.genes

        # gene_annotation numeric columns
        if ann is not None and isinstance(ann, dict):
            ann_cols = ann.get("columns", [])
            ann_cols = [c for c in ann_cols if not c.startswith("aa_")]
            if ann_cols:
                rows.append(_numeric_matrix(ann, genes, ann_cols))

        # gene_constraint numeric columns
        if con is not None and isinstance(con, dict):
            con_cols = con.get("columns", [])
            if con_cols:
                rows.append(_numeric_matrix(con, genes, con_cols))

        # protein_annotation numeric columns
        if prot is not None and isinstance(prot, dict):
            prot_cols = prot.get("columns", [])
            if prot_cols:
                rows.append(_numeric_matrix(prot, genes, prot_cols))

        if rows:
            X = np.concatenate(rows, axis=1)
        else:
            X = np.zeros((n_genes, 1), dtype=float)

        # Standardize each column (nan-aware), fill nans with 0 after centering
        with np.errstate(invalid="ignore"):
            col_mean = np.nanmean(X, axis=0)
            col_std = np.nanstd(X, axis=0)
        col_mean = np.where(np.isfinite(col_mean), col_mean, 0.0)
        col_std = np.where(np.isfinite(col_std) & (col_std > 1e-8), col_std, 1.0)
        Xs = (X - col_mean) / col_std
        Xs = np.where(np.isfinite(Xs), Xs, 0.0)

        # Random projection
        rng = np.random.RandomState(seed)
        d = Xs.shape[1]
        R = rng.normal(0.0, 1.0 / np.sqrt(max(d, 1)), size=(d, n_comp))
        proj = Xs @ R

        # Scale projections to reasonable range
        pstd = proj.std(axis=0)
        pstd = np.where(pstd > 1e-8, pstd, 1.0)
        proj = proj / pstd
        proj = np.where(np.isfinite(proj), proj, 0.0)
        return proj
