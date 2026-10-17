import numpy as np
from genemila.features.api import Feature, register

@register
class FullAnnotationProjectionWithProteinE645(Feature):
    name = "full_annotation_projection_with_protein_e645"
    version = 1
    description = ("Dot product between random projections of concatenated standardized "
                   "gene + protein annotation vectors for the perturbation target and gene g.")
    rationale = ("Random projections of high-dimensional annotations capture holistic gene "
                 "representations; adding protein features adds functional dimensions.")
    inputs = ["knowledge", "target_indices"]
    params = {"n_components": 50, "seed": 645}
    dim = 1

    def _build_matrix(self, ctx):
        if "ann_mat" in ctx.cache:
            return ctx.cache["ann_mat"]
        n = ctx.n_genes
        cols = []
        ga = ctx.knowledge("gene_annotation")
        if ga is not None and isinstance(ga, dict) and "genes" in ga:
            gcols = ga.get("columns", [])
            ggenes = ga["genes"]
            # numeric columns only (skip aa_* handled separately, but they are numeric too)
            for ci, cname in enumerate(gcols):
                vals = np.full(n, np.nan, dtype=float)
                any_ok = False
                for gi, gene in enumerate(ctx.genes):
                    row = ggenes.get(gene)
                    if row is None:
                        continue
                    try:
                        v = row[ci]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        vals[gi] = fv
                        any_ok = True
                if any_ok:
                    cols.append(vals)
        pa = ctx.knowledge("protein_annotation")
        if pa is not None and isinstance(pa, dict) and "genes" in pa:
            pcols = pa.get("columns", [])
            pgenes = pa["genes"]
            for ci, cname in enumerate(pcols):
                if cname == "protein_length":
                    continue  # keep? include; but skip to avoid scale issues? include all numeric
                vals = np.full(n, np.nan, dtype=float)
                any_ok = False
                for gi, gene in enumerate(ctx.genes):
                    row = pgenes.get(gene)
                    if row is None:
                        continue
                    try:
                        v = row[ci]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        vals[gi] = fv
                        any_ok = True
                if any_ok:
                    cols.append(vals)
        if not cols:
            mat = np.zeros((n, 1), dtype=float)
        else:
            mat = np.column_stack(cols)
        # impute nan with column mean, then z-score
        with np.errstate(invalid="ignore"):
            col_mean = np.nanmean(mat, axis=0)
        col_mean = np.where(np.isfinite(col_mean), col_mean, 0.0)
        inds = np.where(~np.isfinite(mat))
        mat[inds] = np.take(col_mean, inds[1])
        mu = mat.mean(axis=0)
        sd = mat.std(axis=0)
        sd = np.where(sd > 1e-8, sd, 1.0)
        mat = (mat - mu) / sd
        mat = np.nan_to_num(mat, nan=0.0, posinf=0.0, neginf=0.0)
        ctx.cache["ann_mat"] = mat
        return mat

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        mat = self._build_matrix(ctx)
        d = mat.shape[1]
        n_comp = int(params.get("n_components", self.params["n_components"]))
        seed = int(params.get("seed", self.params["seed"]))
        rng = np.random.RandomState(seed)
        R = rng.standard_normal((d, n_comp)) / np.sqrt(max(n_comp, 1))
        proj = mat @ R  # (n_genes, n_comp)
        out = np.zeros((len(perts), n, 1), dtype=float)
        for i, p in enumerate(perts):
            tidx = ctx.target_indices(p)
            if not tidx:
                continue
            tvec = proj[tidx].mean(axis=0)
            out[i, :, 0] = proj @ tvec
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
