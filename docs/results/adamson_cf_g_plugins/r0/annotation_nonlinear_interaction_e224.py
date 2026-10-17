import numpy as np
from genemila.features.api import Feature, register


@register
class AnnotationNonlinearInteractionE224(Feature):
    name = "annotation_nonlinear_interaction_e224"
    version = 1
    description = (
        "Per (p,g): sum over selected annotation columns of standardized "
        "target annotation * standardized gene annotation, plus a term of "
        "target annotation times gene control expression mean."
    )
    rationale = (
        "Multiplicative interactions between specific biologically relevant "
        "annotation features (GC content, CpG observed/expected, exon count) "
        "of the perturbation target and the candidate gene may capture "
        "condition-specific effects better than random projections."
    )
    inputs = ["control_mean", "target_genes", "knowledge:gene_annotation"]
    params = {
        "annotation_columns": ["gc_cds", "cpg_oe_promoter", "n_exons"],
        "include_expression_term": True,
        "expression_weight": 0.5,
    }
    dim = 1

    def _load_annotation(self, ctx, columns):
        cache = ctx.cache
        key = ("anno_e224", tuple(columns))
        if key in cache:
            return cache[key]
        anno = ctx.knowledge("gene_annotation")
        n_genes = ctx.n_genes
        mat = np.full((n_genes, len(columns)), np.nan, dtype=np.float64)
        if anno is not None:
            genes = anno.get("genes", {})
            col_names = anno.get("columns", [])
            col_idx = {}
            for j, c in enumerate(col_names):
                col_idx[c] = j
            for gi, g in enumerate(ctx.genes):
                vals = genes.get(g)
                if vals is None:
                    continue
                for k, c in enumerate(columns):
                    j = col_idx.get(c)
                    if j is None or j >= len(vals):
                        continue
                    v = vals[j]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        mat[gi, k] = fv
        # standardize each column using available values
        std_mat = np.zeros_like(mat)
        for k in range(mat.shape[1]):
            col = mat[:, k]
            mask = np.isfinite(col)
            if mask.sum() >= 2:
                mu = col[mask].mean()
                sd = col[mask].std()
                if sd > 1e-12:
                    std_mat[mask, k] = (col[mask] - mu) / sd
                else:
                    std_mat[mask, k] = 0.0
        cache[key] = std_mat
        return std_mat

    def compute(self, ctx, perts, params):
        columns = list(params.get("annotation_columns",
                                 ["gc_cds", "cpg_oe_promoter", "n_exons"]))
        include_expr = bool(params.get("include_expression_term", True))
        expr_w = float(params.get("expression_weight", 0.5))

        std_mat = self._load_annotation(ctx, columns)
        n_genes = ctx.n_genes
        n_cols = std_mat.shape[1]

        # standardized control expression mean
        cm = np.asarray(ctx.control_mean, dtype=np.float64)
        cm_std = np.zeros_like(cm)
        mask = np.isfinite(cm)
        if mask.sum() >= 2:
            mu = cm[mask].mean()
            sd = cm[mask].std()
            if sd > 1e-12:
                cm_std[mask] = (cm[mask] - mu) / sd

        out = np.zeros((len(perts), n_genes, 1), dtype=np.float64)

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            t_idx = [ctx.gene_index[g] for g in tgenes if g in ctx.gene_index]
            if not t_idx:
                continue
            # target annotation vector: average over target genes
            tvec = np.zeros(n_cols, dtype=np.float64)
            for gi in t_idx:
                tvec += std_mat[gi]
            tvec /= float(len(t_idx))

            # pairwise product with gene annotation vector
            # std_mat: (n_genes, n_cols); tvec: (n_cols,)
            gene_term = std_mat @ tvec  # (n_genes,)

            row = gene_term.copy()

            if include_expr and expr_w != 0.0:
                # target expression mean (standardized) times gene expression mean
                t_expr = cm_std[t_idx].mean()
                row = row + expr_w * t_expr * cm_std

            out[i, :, 0] = row

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
