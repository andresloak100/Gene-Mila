import numpy as np
from genemila.features.api import Feature, register


@register
class RandomProjectionAnnotationPPI(Feature):
    name = "random_projection_annotation_ppi_e525_e539"
    version = 1
    description = (
        "Random projection of standardized gene annotation concatenated with a "
        "PPI diffusion score from perturbation target to each gene, reduced to a scalar."
    )
    rationale = (
        "A random projection compresses high-dimensional gene annotation plus network "
        "diffusion into a dense latent score, capturing nonlinear functional similarity "
        "between the perturbed target and each gene."
    )
    inputs = ["control_mean", "knowledge", "target_indices"]
    params = {"n_components": 20, "random_state": 42, "diffusion_steps": 3}
    dim = 1

    def _build_annotation_matrix(self, ctx, params):
        cache = ctx.cache
        key = ("rp_ann_mat_e539",)
        if key in cache:
            return cache[key]

        n = ctx.n_genes
        cols = []

        # gene_annotation
        ann = ctx.knowledge("gene_annotation")
        if ann is not None and "genes" in ann:
            gene_cols = ann.get("columns", [])
            genes = ann["genes"]
            mat = np.full((n, len(gene_cols)), np.nan, dtype=np.float64)
            for i, g in enumerate(ctx.genes):
                vals = genes.get(g)
                if vals is None:
                    continue
                for j in range(min(len(gene_cols), len(vals))):
                    v = vals[j]
                    if v is None:
                        continue
                    try:
                        mat[i, j] = float(v)
                    except (TypeError, ValueError):
                        pass
            cols.append(mat)

        # gene_constraint
        cons = ctx.knowledge("gene_constraint")
        if cons is not None and "genes" in cons:
            gene_cols = cons.get("columns", [])
            genes = cons["genes"]
            mat = np.full((n, len(gene_cols)), np.nan, dtype=np.float64)
            for i, g in enumerate(ctx.genes):
                vals = genes.get(g)
                if vals is None:
                    continue
                for j in range(min(len(gene_cols), len(vals))):
                    v = vals[j]
                    if v is None:
                        continue
                    try:
                        mat[i, j] = float(v)
                    except (TypeError, ValueError):
                        pass
            cols.append(mat)

        # protein_annotation
        prot = ctx.knowledge("protein_annotation")
        if prot is not None and "genes" in prot:
            gene_cols = prot.get("columns", [])
            genes = prot["genes"]
            mat = np.full((n, len(gene_cols)), np.nan, dtype=np.float64)
            for i, g in enumerate(ctx.genes):
                vals = genes.get(g)
                if vals is None:
                    continue
                for j in range(min(len(gene_cols), len(vals))):
                    v = vals[j]
                    if v is None:
                        continue
                    try:
                        mat[i, j] = float(v)
                    except (TypeError, ValueError):
                        pass
            cols.append(mat)

        if not cols:
            ann_mat = np.zeros((n, 1), dtype=np.float64)
        else:
            ann_mat = np.concatenate(cols, axis=1)

        # standardize, impute nan with column mean
        col_mean = np.nanmean(ann_mat, axis=0)
        col_mean = np.where(np.isfinite(col_mean), col_mean, 0.0)
        inds = np.where(~np.isfinite(ann_mat))
        ann_mat[inds] = np.take(col_mean, inds[1])
        col_std = ann_mat.std(axis=0)
        col_std = np.where(col_std > 1e-8, col_std, 1.0)
        ann_std = (ann_mat - ann_mat.mean(axis=0)) / col_std

        cache[key] = ann_std
        return ann_std

    def _build_ppi_adjacency(self, ctx):
        cache = ctx.cache
        key = ("rp_ppi_adj_e539",)
        if key in cache:
            return cache[key]

        n = ctx.n_genes
        net = ctx.knowledge("ppi_network")
        adj = np.zeros((n, n), dtype=np.float64)
        if net is not None:
            for entry in net:
                try:
                    a, b, w = entry[0], entry[1], float(entry[2])
                except (IndexError, TypeError, ValueError):
                    continue
                ia = ctx.gene_index.get(a)
                ib = ctx.gene_index.get(b)
                if ia is None or ib is None:
                    continue
                if w > adj[ia, ib]:
                    adj[ia, ib] = w
                    adj[ib, ia] = w
        cache[key] = adj
        return adj

    def compute(self, ctx, perts, params):
        n_comp = int(params.get("n_components", 20))
        seed = int(params.get("random_state", 42))
        steps = int(params.get("diffusion_steps", 3))

        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1), dtype=np.float64)

        ann_std = self._build_annotation_matrix(ctx, params)
        adj = self._build_ppi_adjacency(ctx)

        # normalize adjacency for diffusion
        deg = adj.sum(axis=1)
        deg = np.where(deg > 1e-12, deg, 1.0)
        inv_deg = 1.0 / deg
        # P = D^-1 A
        def diffuse(vec):
            v = vec.astype(np.float64).copy()
            for _ in range(steps):
                v = inv_deg * (adj @ v)
            return v

        # Build projection matrix (Gaussian random projection)
        n_feat = ann_std.shape[1] + 1  # annotation + diffusion scalar
        rng = np.random.RandomState(seed)
        proj = rng.normal(0.0, 1.0 / np.sqrt(n_comp), size=(n_feat, n_comp))

        cache = ctx.cache

        for i, p in enumerate(perts):
            tkey = ("rp_target_vec_e539", p)
            if tkey in cache:
                diff_vec = cache[tkey]
            else:
                targets = ctx.target_indices(p)
                seed_vec = np.zeros(n, dtype=np.float64)
                if targets:
                    seed_vec[targets] = 1.0
                    diff_vec = diffuse(seed_vec)
                else:
                    diff_vec = np.zeros(n, dtype=np.float64)
                cache[tkey] = diff_vec

            # combine annotation + diffusion
            combined = np.concatenate(
                [ann_std, diff_vec[:, None]], axis=1
            )  # (n, n_feat)
            proj_vals = combined @ proj  # (n, n_comp)
            out[i, :, 0] = proj_vals.mean(axis=1)

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
