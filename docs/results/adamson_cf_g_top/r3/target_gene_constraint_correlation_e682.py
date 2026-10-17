import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGeneConstraintCorrelationE682(Feature):
    name = "target_gene_constraint_correlation_e682"
    version = 1
    description = (
        "Pearson correlation between the target gene's and gene g's LOEUF "
        "(and related constraint) profiles across all genes in gene_constraint."
    )
    rationale = (
        "Genes with similar essentiality/constraint profiles may respond "
        "similarly to perturbations; constraint metrics provide a shared "
        "essentiality axis."
    )
    inputs = ["gene_constraint", "target_indices"]
    params = {"default_value": 0.0}
    dim = 1

    def _build_matrix(self, ctx):
        cached = ctx.cache.get("_e682_matrix")
        if cached is not None:
            return cached

        kc = ctx.knowledge("gene_constraint")
        n = ctx.n_genes
        default = 0.0

        # Collect numeric constraint columns
        cols = None
        genes_data = {}
        if kc is not None:
            cols = kc.get("columns", None)
            genes_data = kc.get("genes", {}) or {}

        if cols:
            ncol = len(cols)
        else:
            ncol = 0

        mat = np.full((n, max(ncol, 1)), default, dtype=float)
        present = np.zeros(n, dtype=bool)

        if ncol > 0 and genes_data:
            for gi, g in enumerate(ctx.genes):
                vals = genes_data.get(g)
                if vals is None:
                    continue
                row = np.full(ncol, np.nan, dtype=float)
                ok = False
                for j in range(min(ncol, len(vals))):
                    v = vals[j]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        row[j] = fv
                        ok = True
                if ok:
                    # fill missing with column means later; store raw
                    mat[gi, :] = row
                    present[gi] = True

        # Replace NaNs with column means over present rows
        if present.any():
            sub = mat[present]
            with np.errstate(invalid="ignore"):
                col_means = np.nanmean(sub, axis=0)
            col_means = np.where(np.isfinite(col_means), col_means, default)
            nan_mask = ~np.isfinite(mat)
            mat[nan_mask] = np.take(col_means, np.where(nan_mask)[1])
        else:
            mat[:] = default

        # Standardize columns (z-score) for correlation
        mu = mat.mean(axis=0, keepdims=True)
        sd = mat.std(axis=0, keepdims=True)
        sd = np.where(sd > 1e-12, sd, 1.0)
        z = (mat - mu) / sd

        # Normalize rows to unit L2 for cosine == correlation
        norms = np.linalg.norm(z, axis=1, keepdims=True)
        norms = np.where(norms > 1e-12, norms, 1.0)
        zn = z / norms

        ctx.cache["_e682_matrix"] = zn
        return zn

    def compute(self, ctx, perts, params):
        default = float(params.get("default_value", 0.0))
        zn = self._build_matrix(ctx)
        n = ctx.n_genes
        out = np.full((len(perts), n, 1), default, dtype=float)

        # Precompute target rows
        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            # Use first target index (single-gene targets)
            ti = tgt_idx[0]
            if ti < 0 or ti >= n:
                continue
            tvec = zn[ti]  # (ncol,)
            # cosine similarity of z-scored rows == Pearson-ish correlation
            sims = zn @ tvec  # (n_genes,)
            sims = np.where(np.isfinite(sims), sims, default)
            out[i, :, 0] = sims

        return out
