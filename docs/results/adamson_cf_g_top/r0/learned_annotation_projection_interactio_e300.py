import numpy as np
from genemila.features.api import Feature, register


@register
class LearnedAnnotationProjectionInteractionE300(Feature):
    name = "learned_annotation_projection_interactio_e300"
    version = 1
    description = ("Dot product between a learned linear projection of the target gene's "
                   "annotation vector and the same projection of gene g's annotation vector.")
    rationale = ("Functional similarity between the perturbed gene and each gene g, measured in a "
                 "low-rank space learned from annotation->response relationships, modulates the "
                 "response; a learned projection should capture relevant dimensions better than "
                 "random projections.")
    inputs = ["control_cells", "train_delta", "knowledge"]
    params = {"projection_dim": 20, "method": "ridge_coef", "ridge_alpha": 1.0}
    dim = 1

    def _build_annotation_matrix(self, ctx):
        cache = ctx.cache
        key = "_e300_annot"
        if key in cache:
            return cache[key]

        n_genes = ctx.n_genes
        gene_index = ctx.gene_index
        cols = []

        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes = ann.get("genes", {})
            columns = ann.get("columns", [])
            # numeric annotation columns
            numeric_cols = [c for c in columns if not c.startswith("aa_")]
            mat = np.full((n_genes, len(numeric_cols)), np.nan, dtype=np.float64)
            for sym, vals in genes.items():
                gi = gene_index.get(sym)
                if gi is None:
                    continue
                if not isinstance(vals, (list, tuple)):
                    continue
                for j, c in enumerate(numeric_cols):
                    try:
                        ci = columns.index(c)
                        v = vals[ci]
                    except (ValueError, IndexError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        mat[gi, j] = fv
            cols.append(mat)

        prot = ctx.knowledge("protein_annotation")
        if prot is not None:
            genes = prot.get("genes", {})
            pcols = prot.get("columns", [])
            mat = np.full((n_genes, len(pcols)), np.nan, dtype=np.float64)
            for sym, vals in genes.items():
                gi = gene_index.get(sym)
                if gi is None or not isinstance(vals, (list, tuple)):
                    continue
                for j in range(min(len(pcols), len(vals))):
                    v = vals[j]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        mat[gi, j] = fv
            cols.append(mat)

        cons = ctx.knowledge("gene_constraint")
        if cons is not None:
            genes = cons.get("genes", {})
            ccols = cons.get("columns", [])
            mat = np.full((n_genes, len(ccols)), np.nan, dtype=np.float64)
            for sym, vals in genes.items():
                gi = gene_index.get(sym)
                if gi is None or not isinstance(vals, (list, tuple)):
                    continue
                for j in range(min(len(ccols), len(vals))):
                    v = vals[j]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        mat[gi, j] = fv
            cols.append(mat)

        if len(cols) == 0:
            A = np.zeros((n_genes, 1), dtype=np.float64)
        else:
            A = np.concatenate(cols, axis=1)

        # Column-wise standardisation with mean imputation
        col_mean = np.nanmean(A, axis=0)
        col_mean = np.where(np.isfinite(col_mean), col_mean, 0.0)
        inds = np.where(~np.isfinite(A))
        A[inds] = np.take(col_mean, inds[1])
        col_std = A.std(axis=0)
        col_std = np.where(col_std > 1e-8, col_std, 1.0)
        A = (A - col_mean) / col_std
        A = np.nan_to_num(A, nan=0.0, posinf=0.0, neginf=0.0)

        cache[key] = A
        return A

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        n_perts = len(perts)
        out = np.zeros((n_perts, n_genes, 1), dtype=np.float64)

        A = self._build_annotation_matrix(ctx)
        n_feat = A.shape[1]
        if n_feat == 0:
            return out

        proj_dim = int(params.get("projection_dim", 20))
        proj_dim = max(1, min(proj_dim, n_feat, max(1, n_genes - 1)))
        alpha = float(params.get("ridge_alpha", 1.0))

        # Fit projection on training deltas (leave out the current pert per row).
        cache = ctx.cache
        proj_key = "_e300_proj"
        fit_key = "_e300_fit"
        # We fit per-perturbation to respect leakage rule. Cache by exclude id.
        for i, p in enumerate(perts):
            ck = (fit_key, p)
            if ck in cache:
                P = cache[ck]
            else:
                tp, D = ctx.train_delta(exclude=p)
                if D is None or D.shape[0] == 0:
                    P = np.zeros((n_feat, proj_dim), dtype=np.float64)
                else:
                    D = np.asarray(D, dtype=np.float64)
                    D = np.nan_to_num(D, nan=0.0, posinf=0.0, neginf=0.0)
                    # Map each training pert to its target gene annotation vector
                    X_rows = []
                    y_rows = []
                    for ti, tp_id in enumerate(tp):
                        tg = ctx.target_indices(tp_id)
                        if len(tg) == 0:
                            continue
                        # average annotation of targeted genes
                        xv = A[tg].mean(axis=0)
                        X_rows.append(xv)
                        y_rows.append(D[ti])
                    if len(X_rows) == 0:
                        P = np.zeros((n_feat, proj_dim), dtype=np.float64)
                    else:
                        X = np.asarray(X_rows, dtype=np.float64)
                        Y = np.asarray(y_rows, dtype=np.float64)
                        # Ridge regression: B = (X^T X + alpha I)^-1 X^T Y
                        XtX = X.T @ X + alpha * np.eye(n_feat)
                        try:
                            XtY = X.T @ Y
                            B = np.linalg.solve(XtX, XtY)
                        except np.linalg.LinAlgError:
                            B = np.linalg.lstsq(XtX, X.T @ Y, rcond=None)[0]
                        B = np.nan_to_num(B, nan=0.0, posinf=0.0, neginf=0.0)
                        # Reduce to proj_dim via SVD of B (n_feat x n_genes)
                        try:
                            U, S, Vt = np.linalg.svd(B, full_matrices=False)
                            k = min(proj_dim, U.shape[1])
                            P = U[:, :k] * S[:k]
                        except np.linalg.LinAlgError:
                            P = np.zeros((n_feat, proj_dim), dtype=np.float64)
                        if P.shape[1] < proj_dim:
                            pad = np.zeros((n_feat, proj_dim - P.shape[1]))
                            P = np.concatenate([P, pad], axis=1)
                cache[ck] = P

            # Project all gene annotations into learned space
            Z = A @ P  # (n_genes, proj_dim)

            tg = ctx.target_indices(p)
            if len(tg) == 0:
                continue
            tvec = Z[tg].mean(axis=0)  # (proj_dim,)
            # Dot product with every gene
            out[i, :, 0] = Z @ tvec

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
