import numpy as np
from genemila.features.api import Feature, register


@register
class RandomProjectionGeneAnnotationE124(Feature):
    name = "random_projection_gene_annotation_e124"
    version = 1
    description = (
        "Random Gaussian projection of the standardized per-gene numeric "
        "annotation matrix into k dimensions, broadcast identically across "
        "perturbations."
    )
    rationale = (
        "Gene annotation contains many numeric columns; a low-dimensional "
        "random projection summarizes their joint structure into a few dense "
        "features that may capture latent gene properties not captured by "
        "individual columns."
    )
    inputs = ["knowledge"]
    params = {"k": 10, "seed": 42}
    dim = 10

    def _build_annotation_matrix(self, ctx, params):
        """Cache the projected annotation matrix keyed by (k, seed)."""
        k = int(params.get("k", 10))
        seed = int(params.get("seed", 42))
        cache_key = ("rpgeneann_e124", k, seed)
        if cache_key in ctx.cache:
            return ctx.cache[cache_key]

        n_genes = ctx.n_genes
        # Collect numeric annotation columns from the available knowledge bundles.
        columns = []  # each entry: np.ndarray of shape (n_genes,)
        seen_signatures = set()

        # We iterate over known bundles that carry per-gene numeric "genes" tables.
        bundle_names = []
        try:
            bundle_names = list(ctx.available_knowledge())
        except Exception:
            bundle_names = []

        # Prefer the specific bundles described in the data; fall back to all.
        preferred = [
            "gene_annotation",
            "gene_constraint",
            "protein_annotation",
        ]
        ordered = [b for b in preferred if b in bundle_names]
        ordered += [b for b in bundle_names if b not in ordered]

        for bname in ordered:
            try:
                bundle = ctx.knowledge(bname)
            except Exception:
                bundle = None
            if not isinstance(bundle, dict):
                continue
            gene_table = bundle.get("genes")
            if not isinstance(gene_table, dict):
                continue
            col_names = bundle.get("columns")
            if not isinstance(col_names, list):
                # Cannot interpret ordering; skip this bundle.
                continue

            for ci, colname in enumerate(col_names):
                col = np.full(n_genes, np.nan, dtype=np.float64)
                any_val = False
                for gi, g in enumerate(ctx.genes):
                    vals = gene_table.get(g)
                    if vals is None:
                        continue
                    try:
                        v = vals[ci]
                    except Exception:
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except Exception:
                        continue
                    if np.isfinite(fv):
                        col[gi] = fv
                        any_val = True
                if not any_val:
                    continue
                # Deduplicate identical columns (e.g. shared annotation tables).
                sig = (colname, tuple(np.round(col, 6).tolist()))
                if sig in seen_signatures:
                    continue
                seen_signatures.add(sig)
                columns.append(col)

        if columns:
            X = np.column_stack(columns).astype(np.float64)
        else:
            X = np.zeros((n_genes, 0), dtype=np.float64)

        # Standardize columns (mean 0, unit std); impute NaNs with column mean.
        if X.shape[1] > 0:
            col_means = np.nanmean(X, axis=0)
            col_means = np.where(np.isfinite(col_means), col_means, 0.0)
            nan_mask = ~np.isfinite(X)
            if nan_mask.any():
                X[nan_mask] = np.take(col_means, np.where(nan_mask)[1])
            col_std = X.std(axis=0)
            col_std = np.where(col_std > 1e-12, col_std, 1.0)
            X = (X - col_means) / col_std

            rng = np.random.default_rng(seed)
            R = rng.standard_normal((X.shape[1], k))
            # Normalize projection directions to keep scale reasonable.
            norms = np.linalg.norm(R, axis=0)
            norms = np.where(norms > 1e-12, norms, 1.0)
            R = R / norms
            proj = X @ R  # (n_genes, k)
        else:
            proj = np.zeros((n_genes, k), dtype=np.float64)

        proj = np.nan_to_num(proj, nan=0.0, posinf=0.0, neginf=0.0)
        ctx.cache[cache_key] = proj
        return proj

    def compute(self, ctx, perts, params):
        k = int(params.get("k", self.params["k"]))
        proj = self._build_annotation_matrix(ctx, params)  # (n_genes, k_used)

        n_perts = len(perts)
        out = np.zeros((n_perts, ctx.n_genes, k), dtype=np.float64)

        # Broadcast the same per-gene projection to every perturbation row.
        if proj.shape[1] >= k:
            block = proj[:, :k]
        else:
            block = np.zeros((ctx.n_genes, k), dtype=np.float64)
            block[:, : proj.shape[1]] = proj
        out[:, :, :] = block[None, :, :]

        return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
