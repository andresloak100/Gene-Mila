import numpy as np
from genemila.features.api import Feature, register


@register
class RandomProjectionAnnotationTargetSimi(Feature):
    name = "random_projection_annotation_target_simi_e692"
    version = 1
    description = "Cosine similarity between a random projection of gene g's annotation vector and the mean projected annotation of p's targets."
    rationale = "High-dimensional annotation data may contain latent structure relevant to perturbation response; a random projection gives a low-dimensional similarity between a gene and a perturbation's targets."
    inputs = ["control_cells"]
    params = {"n_components": 50, "random_state": 42}
    dim = 1

    def _build_annotation_matrix(self, ctx):
        n = ctx.n_genes
        cols = []

        def add_table(name, col_names, transform=None):
            data = ctx.knowledge(name)
            if not isinstance(data, dict):
                return
            genes = data.get("genes", {})
            if not isinstance(genes, dict):
                return
            for cname in col_names:
                vec = np.full(n, np.nan, dtype=float)
                any_val = False
                for i, g in enumerate(ctx.genes):
                    entry = genes.get(g)
                    if entry is None:
                        continue
                    try:
                        idx = data["columns"].index(cname)
                    except (KeyError, ValueError):
                        return
                    try:
                        v = entry[idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        v = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(v):
                        vec[i] = v
                        any_val = True
                if any_val:
                    cols.append(vec)

        # gene_annotation
        ga = ctx.knowledge("gene_annotation")
        if isinstance(ga, dict) and "columns" in ga:
            numeric_cols = [c for c in ga["columns"] if not c.startswith("aa_")]
            add_table("gene_annotation", numeric_cols)

        # gene_constraint
        gc = ctx.knowledge("gene_constraint")
        if isinstance(gc, dict) and "columns" in gc:
            add_table("gene_constraint", list(gc["columns"]))

        # protein_annotation
        pa = ctx.knowledge("protein_annotation")
        if isinstance(pa, dict) and "columns" in pa:
            add_table("protein_annotation", list(pa["columns"]))

        if not cols:
            return None

        mat = np.column_stack(cols)
        # impute nan with column median (or 0)
        for j in range(mat.shape[1]):
            col = mat[:, j]
            mask = np.isfinite(col)
            if mask.any():
                med = np.median(col[mask])
            else:
                med = 0.0
            col[~mask] = med
            mat[:, j] = col

        # standardise columns
        mean = mat.mean(axis=0)
        std = mat.std(axis=0)
        std[std < 1e-8] = 1.0
        mat = (mat - mean) / std
        return mat

    def compute(self, ctx, perts, params):
        n_components = int(params.get("n_components", 50))
        random_state = int(params.get("random_state", 42))

        cache = ctx.cache
        key = ("rp_ann", n_components, random_state)
        if key in cache:
            proj = cache[key]
        else:
            mat = self._build_annotation_matrix(ctx)
            if mat is None:
                proj = np.zeros((ctx.n_genes, n_components), dtype=float)
            else:
                rng = np.random.RandomState(random_state)
                R = rng.normal(0.0, 1.0 / np.sqrt(n_components),
                               size=(mat.shape[1], n_components))
                proj = mat @ R
            # normalise rows for cosine
            norms = np.linalg.norm(proj, axis=1, keepdims=True)
            norms[norms < 1e-12] = 1.0
            proj = proj / norms
            cache[key] = proj

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            tgt_vec = proj[tgt_idx].mean(axis=0)
            tn = np.linalg.norm(tgt_vec)
            if tn < 1e-12:
                continue
            tgt_vec = tgt_vec / tn
            sims = proj @ tgt_vec
            out[i, :, 0] = sims
        return out
