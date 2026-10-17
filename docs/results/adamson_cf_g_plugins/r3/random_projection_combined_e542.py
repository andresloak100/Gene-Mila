import numpy as np
from genemila.features.api import Feature, register


@register
class RandomProjectionCombinedE542(Feature):
    name = "random_projection_combined_e542"
    version = 1
    description = ("10 random Gaussian projections of a per-(pert,gene) design matrix "
                   "combining static gene annotation columns and target-level response statistics.")
    rationale = ("Random projections of combined static + target-response features can capture "
                 "latent interactions not represented by individual features; used as extra ridge inputs.")
    inputs = ["train_delta", "gene_annotation", "protein_annotation", "gene_constraint"]
    params = {"n_components": 10, "random_state": 42}
    dim = 10

    def _build_gene_static(self, ctx, params):
        cache = ctx.cache
        key = ("rpc_static", self.name, params.get("random_state", 42))
        if key in cache:
            return cache[key]

        n_genes = ctx.n_genes
        cols = []

        # ---- gene_annotation ----
        ann = ctx.knowledge("gene_annotation")
        ann_cols = ["gene_span_kb", "n_transcripts", "n_exons", "transcript_length",
                    "cds_length", "utr5_length", "utr3_length", "intron_length_kb",
                    "gc_cds", "gc_utr3", "gc_promoter", "cpg_oe_promoter",
                    "n_upstream_atg", "nearest_tss_kb", "n_tss_within_100kb"]
        if ann and "genes" in ann:
            gmap = ann["genes"]
            ncol = len(ann.get("columns", ann_cols))
            mat = np.full((n_genes, ncol), np.nan, dtype=np.float64)
            for i, g in enumerate(ctx.genes):
                vals = gmap.get(g)
                if vals is None:
                    continue
                for j in range(min(ncol, len(vals))):
                    v = vals[j]
                    if v is not None:
                        try:
                            mat[i, j] = float(v)
                        except (TypeError, ValueError):
                            pass
            cols.append(mat)

        # ---- protein_annotation ----
        prot = ctx.knowledge("protein_annotation")
        if prot and "genes" in prot:
            gmap = prot["genes"]
            ncol = len(prot.get("columns", [])) or 13
            mat = np.full((n_genes, ncol), np.nan, dtype=np.float64)
            for i, g in enumerate(ctx.genes):
                vals = gmap.get(g)
                if vals is None:
                    continue
                for j in range(min(ncol, len(vals))):
                    v = vals[j]
                    if v is not None:
                        try:
                            mat[i, j] = float(v)
                        except (TypeError, ValueError):
                            pass
            cols.append(mat)

        # ---- gene_constraint ----
        con = ctx.knowledge("gene_constraint")
        if con and "genes" in con:
            gmap = con["genes"]
            ncol = len(con.get("columns", [])) or 5
            mat = np.full((n_genes, ncol), np.nan, dtype=np.float64)
            for i, g in enumerate(ctx.genes):
                vals = gmap.get(g)
                if vals is None:
                    continue
                for j in range(min(ncol, len(vals))):
                    v = vals[j]
                    if v is not None:
                        try:
                            mat[i, j] = float(v)
                        except (TypeError, ValueError):
                            pass
            cols.append(mat)

        if cols:
            static = np.concatenate(cols, axis=1)
        else:
            static = np.zeros((n_genes, 1), dtype=np.float64)

        # impute NaN with column mean (0 if all-nan), then standardize
        col_mean = np.nanmean(static, axis=0)
        col_mean = np.where(np.isfinite(col_mean), col_mean, 0.0)
        inds = np.where(~np.isfinite(static))
        static[inds] = np.take(col_mean, inds[1])
        col_std = static.std(axis=0)
        col_std = np.where(col_std > 1e-8, col_std, 1.0)
        static = (static - static.mean(axis=0)) / col_std

        cache[key] = static
        return static

    def compute(self, ctx, perts, params):
        n_components = int(params.get("n_components", 10))
        random_state = int(params.get("random_state", 42))
        n_genes = ctx.n_genes

        static = self._build_gene_static(ctx, params)
        n_static = static.shape[1]

        # target-level response statistics per perturbation (leave-p-out)
        # columns: [mean_delta_target, var_delta_target, std_control_target,
        #           mean_delta_all, var_delta_all, frac_nonzero_target]
        n_target_feats = 6

        # For projection: total feature dim per (p,g) row
        # Row features = static[g] (n_static) + target_stats (n_target_feats)
        # plus interaction-ish term: static[g] * target_stats[0] (mean delta of target)
        n_inter = 1
        total_dim = n_static + n_target_feats + n_inter

        rng = np.random.RandomState(random_state)
        # Gaussian random projection matrix (use sqrt scaling)
        proj = rng.normal(0.0, 1.0 / np.sqrt(total_dim), size=(total_dim, n_components))

        out = np.zeros((len(perts), n_genes, self.dim), dtype=np.float64)

        # precompute control std
        ctrl_std = ctx.control_std
        ctrl_std = np.where(np.isfinite(ctrl_std), ctrl_std, 0.0)

        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)  # (n_train, n_genes)
            if d.shape[0] == 0:
                continue
            d_mean = d.mean(axis=0)  # (n_genes,)
            d_var = d.var(axis=0)
            d_mean_all = float(np.mean(d_mean))
            d_var_all = float(np.mean(d_var))

            t_idx = ctx.target_indices(p)
            if t_idx:
                ti = t_idx[0]
                target_mean = float(d_mean[ti])
                target_var = float(d_var[ti])
                target_ctrl_std = float(ctrl_std[ti])
                target_frac_nonzero = float(np.mean(d[:, ti] != 0.0))
            else:
                target_mean = 0.0
                target_var = 0.0
                target_ctrl_std = 0.0
                target_frac_nonzero = 0.0

            target_feats = np.array(
                [target_mean, target_var, target_ctrl_std,
                 d_mean_all, d_var_all, target_frac_nonzero],
                dtype=np.float64,
            )

            # Build (n_genes, total_dim) matrix
            rows = np.empty((n_genes, total_dim), dtype=np.float64)
            rows[:, :n_static] = static
            rows[:, n_static:n_static + n_target_feats] = target_feats[np.newaxis, :]
            # interaction term: static first column * target mean
            rows[:, n_static + n_target_feats] = static[:, 0] * target_mean

            proj_vals = rows @ proj  # (n_genes, n_components)
            # pad/truncate to self.dim
            m = min(n_components, self.dim)
            out[i, :, :m] = proj_vals[:, :m]
            if m < self.dim:
                out[i, :, m:] = 0.0

        out[~np.isfinite(out)] = 0.0
        return out
