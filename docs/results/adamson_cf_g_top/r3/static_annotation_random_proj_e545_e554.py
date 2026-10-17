import numpy as np
from genemila.features.api import Feature, register


@register
class StaticAnnotationRandomProj(Feature):
    name = "static_annotation_random_proj_e545_e554"
    version = 1
    description = ("10-dim random Gaussian projection of concatenated static gene "
                   "annotation features (gene_annotation, gene_constraint, protein_annotation).")
    rationale = ("A low-dimensional random projection preserves distances of the "
                 "high-dimensional static annotation space and may capture combined "
                 "latent structure relevant to perturbation response.")
    inputs = ["knowledge"]
    params = {"n_components": 10, "random_seed": 42}
    dim = 10

    def _build_matrix(self, ctx, params):
        cache = ctx.cache
        key = ("static_anno_matrix", params.get("n_components", 10),
               params.get("random_seed", 42))
        if key in cache:
            return cache[key]

        genes = ctx.genes
        n_genes = ctx.n_genes
        columns = []

        def add_table(name):
            data = ctx.knowledge(name)
            if not isinstance(data, dict):
                return
            gene_vals = data.get("genes")
            if not isinstance(gene_vals, dict):
                return
            col_names = data.get("columns")
            if col_names is None:
                # fall back: infer width from first present entry
                width = None
                for g in genes:
                    v = gene_vals.get(g)
                    if v is not None:
                        width = len(v)
                        break
                if width is None:
                    return
                col_names = list(range(width))
            n_cols = len(col_names)
            mat = np.full((n_genes, n_cols), np.nan, dtype=float)
            for i, g in enumerate(genes):
                v = gene_vals.get(g)
                if v is None:
                    continue
                for j in range(min(n_cols, len(v))):
                    x = v[j]
                    if x is None:
                        continue
                    try:
                        fx = float(x)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fx):
                        mat[i, j] = fx
            for j in range(n_cols):
                col = mat[:, j]
                finite = np.isfinite(col)
                if not finite.any():
                    continue
                if finite.all():
                    columns.append(col)
                else:
                    mean = col[finite].mean()
                    col = np.where(finite, col, mean)
                    columns.append(col)

        add_table("gene_annotation")
        add_table("gene_constraint")
        add_table("protein_annotation")

        if not columns:
            # degenerate: no static info -> zeros basis
            base = np.zeros((n_genes, 1), dtype=float)
        else:
            base = np.stack(columns, axis=1)

        # standardize columns (guard zero variance)
        mu = base.mean(axis=0)
        sd = base.std(axis=0)
        sd = np.where(sd > 1e-12, sd, 1.0)
        base = (base - mu) / sd

        n_comp = int(params.get("n_components", 10))
        seed = int(params.get("random_seed", 42))
        rng = np.random.RandomState(seed)
        proj = rng.normal(0.0, 1.0 / np.sqrt(max(base.shape[1], 1)),
                          size=(base.shape[1], n_comp))
        result = base @ proj  # (n_genes, n_comp)

        cache[key] = result
        return result

    def compute(self, ctx, perts, params):
        n_comp = int(params.get("n_components", 10))
        mat = self._build_matrix(ctx, params)  # (n_genes, n_comp)
        out = np.zeros((len(perts), ctx.n_genes, n_comp), dtype=float)
        for i in range(len(perts)):
            out[i] = mat
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
