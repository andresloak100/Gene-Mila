import numpy as np
from genemila.features.api import Feature, register


@register
class CombinedAnnotationPPIRandomProjectionE548(Feature):
    name = "combined_annotation_ppi_random_projectio_e548"
    version = 1
    description = ("Random projection of concatenated standardized gene annotation and "
                   "PPI diffusion scores per gene.")
    rationale = ("Combining annotation and network information in a low-dimensional random "
                 "projection may reveal latent structure capturing nonlinear interactions.")
    inputs = ["control_cells", "gene_annotation", "protein_annotation", "gene_constraint",
              "ppi_network"]
    params = {"n_components": 50, "seed": 548, "diffusion_alpha": 0.5, "diffusion_steps": 3}
    dim = 1

    def _build_annotation_matrix(self, ctx):
        cache = ctx.cache
        key = ("e548_anno",)
        if key in cache:
            return cache[key]

        n = ctx.n_genes
        cols = []

        # Control expression summary features
        cm = np.asarray(ctx.control_mean, dtype=float)
        cs = np.asarray(ctx.control_std, dtype=float)
        cols.append(cm)
        cols.append(cs)
        cols.append(cs / (np.abs(cm) + 1e-6))

        # gene_annotation
        ga = ctx.knowledge("gene_annotation")
        if ga is not None and "genes" in ga and "columns" in ga:
            colnames = ga["columns"]
            mat = np.full((n, len(colnames)), np.nan, dtype=float)
            genes_map = ga["genes"]
            for i, g in enumerate(ctx.genes):
                vals = genes_map.get(g)
                if vals is None:
                    continue
                for j in range(min(len(colnames), len(vals))):
                    v = vals[j]
                    if v is not None:
                        try:
                            mat[i, j] = float(v)
                        except (TypeError, ValueError):
                            pass
            # keep a subset of numeric annotation columns to limit dimensionality
            keep = [j for j in range(mat.shape[1]) if np.isfinite(mat[:, j]).any()]
            for j in keep:
                col = mat[:, j]
                if not np.isfinite(col).all():
                    med = np.nanmedian(col)
                    if not np.isfinite(med):
                        med = 0.0
                    col = np.where(np.isfinite(col), col, med)
                cols.append(col)

        # protein_annotation
        pa = ctx.knowledge("protein_annotation")
        if pa is not None and "genes" in pa and "columns" in pa:
            colnames = pa["columns"]
            mat = np.full((n, len(colnames)), np.nan, dtype=float)
            genes_map = pa["genes"]
            for i, g in enumerate(ctx.genes):
                vals = genes_map.get(g)
                if vals is None:
                    continue
                for j in range(min(len(colnames), len(vals))):
                    v = vals[j]
                    if v is not None:
                        try:
                            mat[i, j] = float(v)
                        except (TypeError, ValueError):
                            pass
            keep = [j for j in range(mat.shape[1]) if np.isfinite(mat[:, j]).any()]
            for j in keep:
                col = mat[:, j]
                if not np.isfinite(col).all():
                    med = np.nanmedian(col)
                    if not np.isfinite(med):
                        med = 0.0
                    col = np.where(np.isfinite(col), col, med)
                cols.append(col)

        # gene_constraint
        gc = ctx.knowledge("gene_constraint")
        if gc is not None and "genes" in gc and "columns" in gc:
            colnames = gc["columns"]
            mat = np.full((n, len(colnames)), np.nan, dtype=float)
            genes_map = gc["genes"]
            for i, g in enumerate(ctx.genes):
                vals = genes_map.get(g)
                if vals is None:
                    continue
                for j in range(min(len(colnames), len(vals))):
                    v = vals[j]
                    if v is not None:
                        try:
                            mat[i, j] = float(v)
                        except (TypeError, ValueError):
                            pass
            keep = [j for j in range(mat.shape[1]) if np.isfinite(mat[:, j]).any()]
            for j in keep:
                col = mat[:, j]
                if not np.isfinite(col).all():
                    med = np.nanmedian(col)
                    if not np.isfinite(med):
                        med = 0.0
                    col = np.where(np.isfinite(col), col, med)
                cols.append(col)

        if not cols:
            A = np.zeros((n, 1), dtype=float)
        else:
            A = np.column_stack(cols).astype(float)

        # standardize
        mu = A.mean(axis=0)
        sd = A.std(axis=0)
        sd = np.where(sd > 1e-8, sd, 1.0)
        A = (A - mu) / sd

        cache[key] = A
        return A

    def _ppi_adjacency(self, ctx):
        cache = ctx.cache
        key = ("e548_ppi_adj",)
        if key in cache:
            return cache[key]
        n = ctx.n_genes
        W = np.zeros((n, n), dtype=float)
        ppi = ctx.knowledge("ppi_network")
        if ppi is not None:
            gi = ctx.gene_index
            for entry in ppi:
                try:
                    a, b, w = entry[0], entry[1], float(entry[2])
                except (TypeError, ValueError, IndexError):
                    continue
                ia = gi.get(a)
                ib = gi.get(b)
                if ia is None or ib is None:
                    continue
                W[ia, ib] = max(W[ia, ib], w)
                W[ib, ia] = max(W[ib, ia], w)
        cache[key] = W
        return W

    def _diffusion(self, ctx, params):
        cache = ctx.cache
        key = ("e548_diffusion", params.get("diffusion_alpha", 0.5),
               params.get("diffusion_steps", 3))
        if key in cache:
            return cache[key]
        W = self._ppi_adjacency(ctx)
        n = ctx.n_genes
        deg = W.sum(axis=1)
        deg = np.where(deg > 1e-8, deg, 1.0)
        P = W / deg[:, None]
        alpha = float(params.get("diffusion_alpha", 0.5))
        steps = int(params.get("diffusion_steps", 3))
        S = np.eye(n, dtype=float)
        cur = np.eye(n, dtype=float)
        for _ in range(steps):
            cur = alpha * (P @ cur) + (1.0 - alpha) * np.eye(n, dtype=float)
            S = S + cur
        S = S / (steps + 1)
        cache[key] = S
        return S

    def _projection(self, ctx, dim_in, params):
        cache = ctx.cache
        seed = int(params.get("seed", 548))
        key = ("e548_proj", dim_in, seed)
        if key in cache:
            return cache[key]
        rng = np.random.RandomState(seed)
        R = rng.randn(dim_in, dim_in) / np.sqrt(dim_in)
        cache[key] = R
        return R

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        n_perts = len(perts)
        out = np.zeros((n_perts, n, 1), dtype=float)

        A = self._build_annotation_matrix(ctx)
        S = self._diffusion(ctx, params)

        # Combine: annotation per gene + row of diffusion (PPI diffusion profile)
        # Reduce diffusion to a compact summary via its own projection to avoid huge dims
        rng = np.random.RandomState(int(params.get("seed", 548)) + 7)
        n_comp = int(params.get("n_components", 50))
        proj_dim = max(1, min(n_comp, n))
        R_s = rng.randn(n, proj_dim) / np.sqrt(n)
        S_proj = S @ R_s  # (n, proj_dim)

        F = np.concatenate([A, S_proj], axis=1)  # (n, dA + proj_dim)
        d = F.shape[1]

        # Final random Gaussian projection to n_comp dims
        R = self._projection(ctx, d, params)
        Z = F @ R  # (n, d)

        # For each perturbation, use target genes to build a row; if no target, use mean
        for i, p in enumerate(perts):
            tgt = ctx.target_indices(p)
            if len(tgt) > 0:
                z = Z[tgt].mean(axis=0)
            else:
                z = Z.mean(axis=0)
            # gene-wise scalar: dot of gene projection with perturbation projection
            # Use a deterministic perturbation-specific vector derived from target/mean
            out[i, :, 0] = Z @ (z / (np.linalg.norm(z) + 1e-8))

        # Ensure finite
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
