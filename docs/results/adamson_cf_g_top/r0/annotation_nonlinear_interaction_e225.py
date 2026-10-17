import numpy as np
from genemila.features.api import Feature, register


@register
class AnnotationNonlinearInteractionE225(Feature):
    name = "annotation_nonlinear_interaction_e225"
    version = 1
    description = (
        "For each (p,g), product of standardized target annotation features and "
        "standardized gene annotation features (pairwise across selected columns), "
        "plus target-annotation times gene control-mean interaction."
    )
    rationale = (
        "Nonlinear multiplicative interactions between biologically relevant annotation "
        "features of the perturbation target and the responding gene may capture "
        "condition-specific effects that linear projections miss."
    )
    inputs = ["knowledge", "control_mean"]
    params = {"annotation_columns": ["gc_cds", "cpg_oe_promoter", "n_exons"]}
    dim = 1

    def _load_annotation(self, ctx, columns):
        key = ("anno_e225", tuple(columns))
        cache = ctx.cache
        if key in cache:
            return cache[key]
        data = ctx.knowledge("gene_annotation")
        mat = np.full((ctx.n_genes, len(columns)), np.nan, dtype=np.float64)
        if data is not None:
            genes = data.get("genes", {})
            col_names = data.get("columns", [])
            col_idx = {}
            for j, c in enumerate(columns):
                if c in col_names:
                    col_idx[j] = col_names.index(c)
            for gi, g in enumerate(ctx.genes):
                vals = genes.get(g)
                if vals is None:
                    continue
                for j, ci in col_idx.items():
                    try:
                        v = vals[ci]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        mat[gi, j] = fv
        # standardize each column (nan-safe)
        norm = np.zeros_like(mat)
        for j in range(mat.shape[1]):
            col = mat[:, j]
            mask = np.isfinite(col)
            if mask.sum() < 2:
                continue
            mu = col[mask].mean()
            sd = col[mask].std()
            if sd <= 0 or not np.isfinite(sd):
                sd = 1.0
            norm[mask, j] = (col[mask] - mu) / sd
        cache[key] = norm
        return norm

    def compute(self, ctx, perts, params):
        columns = list(params.get("annotation_columns", self.params["annotation_columns"]))
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=np.float64)

        anno = self._load_annotation(ctx, columns)
        n_cols = anno.shape[1]
        if n_cols == 0:
            return out

        # gene-side standardized control mean
        cm = np.asarray(ctx.control_mean, dtype=np.float64)
        cm_mask = np.isfinite(cm)
        if cm_mask.sum() >= 2:
            mu = cm[cm_mask].mean()
            sd = cm[cm_mask].std()
            if sd <= 0 or not np.isfinite(sd):
                sd = 1.0
            cm_z = np.zeros_like(cm)
            cm_z[cm_mask] = (cm[cm_mask] - mu) / sd
        else:
            cm_z = np.zeros_like(cm)

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            tgt_vec = anno[tgt_idx, :].mean(axis=0)  # (n_cols,)
            # pairwise product sum: sum_j tgt_j * gene_j
            pairwise = anno @ tgt_vec  # (n_genes,)
            # target annotation mean times gene control mean
            tgt_mean = float(np.nanmean(tgt_vec)) if n_cols > 0 else 0.0
            if not np.isfinite(tgt_mean):
                tgt_mean = 0.0
            interaction = pairwise + tgt_mean * cm_z
            out[i, :, 0] = interaction

        out[~np.isfinite(out)] = 0.0
        return out
