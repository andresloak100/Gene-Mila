import numpy as np
from genemila.features.api import Feature, register


@register
class CoessentialityCorrTargetGene(Feature):
    name = "coessentiality_corr_target_gene_e268"
    version = 1
    description = (
        "Pearson correlation between the essentiality/constraint profile of the "
        "perturbation target and each gene g, using gnomAD LoF constraint metrics "
        "(LOEUF, pLI, oe_lof, etc.) as a multi-dimensional proxy for essentiality."
    )
    rationale = (
        "Genes co-essential with the perturbation target (similar constraint/essentiality "
        "profiles) may be functionally linked and thus more responsive to its perturbation."
    )
    inputs = ["knowledge", "target_indices"]
    params = {"metric": "loeuf"}
    dim = 1

    def _build_profiles(self, ctx, params):
        """Build (n_genes, n_metrics) profile matrix from gnomAD constraint metrics."""
        cache = ctx.cache
        key = "coess_profiles_e268"
        if key in cache:
            return cache[key]

        n = ctx.n_genes
        profiles = np.full((n, 4), np.nan, dtype=float)

        knowledge = ctx.knowledge("gene_constraint")
        if knowledge is None:
            cache[key] = profiles
            return profiles

        cols = knowledge.get("columns", [])
        genes_tbl = knowledge.get("genes", {})
        if not cols or not genes_tbl:
            cache[key] = profiles
            return profiles

        # Identify metric columns of interest
        def col_idx(name):
            try:
                return cols.index(name)
            except ValueError:
                return -1

        idx_loeuf = col_idx("oe_lof_upper")
        idx_pli = col_idx("pLI")
        idx_oelof = col_idx("oe_lof")
        idx_obs = col_idx("obs_lof")

        # Fallbacks if specific names absent: take first few numeric columns
        metric_idxs = [i for i in (idx_loeuf, idx_pli, idx_oelof, idx_obs) if i >= 0]
        if not metric_idxs:
            # use up to 4 columns after the first (assume first is gene id-ish)
            metric_idxs = list(range(min(4, len(cols))))

        for g in ctx.genes:
            vals = genes_tbl.get(g)
            if vals is None:
                continue
            gi = ctx.gene_index[g]
            row = []
            for mi in metric_idxs:
                if mi < len(vals):
                    v = vals[mi]
                    if v is None:
                        row.append(np.nan)
                    else:
                        try:
                            row.append(float(v))
                        except (TypeError, ValueError):
                            row.append(np.nan)
                else:
                    row.append(np.nan)
            # pad/truncate to 4
            while len(row) < 4:
                row.append(np.nan)
            profiles[gi, :] = row[:4]

        cache[key] = profiles
        return profiles

    def _corr_row(self, profile, target_vec):
        """Pearson correlation between target_vec and each row of profile."""
        n = profile.shape[0]
        out = np.zeros(n, dtype=float)

        # Determine valid target dimensions
        tv = np.asarray(target_vec, dtype=float)
        t_valid = np.isfinite(tv)

        if not t_valid.any():
            return out

        # For each gene, compute correlation over dims where both are finite
        # Vectorized: mask invalid as nan
        p = profile.copy()
        # Zero-variance handling per gene
        with np.errstate(invalid="ignore", divide="ignore"):
            # centre using available dims
            pv = np.where(np.isfinite(p), p, np.nan)

            # We'll compute using pairwise finite mask
            # Since dims is small (<=4), do a simple loop over dims contributions
            # but vectorize over genes.
            t_mean = np.nanmean(tv) if t_valid.any() else 0.0
            # Use only dims valid in target
            dims = np.where(t_valid)[0]
            t_sub = tv[dims]
            t_sub_c = t_sub - t_sub.mean()
            t_norm = np.sqrt(np.sum(t_sub_c ** 2))
            if t_norm == 0:
                return out

            p_sub = pv[:, dims]  # (n, k)
            mask = np.isfinite(p_sub)  # (n, k)
            counts = mask.sum(axis=1)

            # gene means over valid dims
            p_filled = np.where(mask, p_sub, 0.0)
            sums = p_filled.sum(axis=1)
            means = np.where(counts > 0, sums / np.maximum(counts, 1), 0.0)

            p_centered = np.where(mask, p_sub - means[:, None], 0.0)

            # numerator: sum over dims of p_centered * t_sub_c (only where mask)
            t_broadcast = t_sub_c[None, :]
            num = np.sum(p_centered * t_broadcast, axis=1)

            # denominators
            p_var = np.sum(p_centered ** 2, axis=1)
            # target variance restricted to dims valid for each gene:
            # sum over dims mask * (t_sub_c^2)
            t_var_per_gene = np.sum(np.where(mask, (t_sub_c[None, :]) ** 2, 0.0), axis=1)

            denom = np.sqrt(p_var * t_var_per_gene)
            valid = denom > 0
            out = np.where(valid, num / np.where(valid, denom, 1.0), 0.0)

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1), dtype=float)

        profiles = self._build_profiles(ctx, params)

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            # Use first target gene
            ti = tgt_idx[0]
            target_vec = profiles[ti, :]
            if not np.isfinite(target_vec).any():
                continue
            corr = self._corr_row(profiles, target_vec)
            out[i, :, 0] = corr

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
