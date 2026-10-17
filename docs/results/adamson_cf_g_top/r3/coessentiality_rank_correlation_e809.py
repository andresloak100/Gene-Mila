import numpy as np
from genemila.features.api import Feature, register

@register
class CoessentialityRankCorrelation(Feature):
    name = "coessentiality_rank_correlation_e809"
    version = 1
    description = ("Spearman rank correlation between essentiality profiles of the "
                   "perturbation target and gene g across available cell lines; 0 if missing.")
    rationale = ("Coessentiality reflects shared functional dependencies; genes with similar "
                 "essentiality profiles respond similarly to perturbation. Rank correlation is "
                 "robust to outliers and scale differences.")
    inputs = ["gene_constraint", "knowledge"]
    params = {"min_overlap": 10}
    dim = 1

    def compute(self, ctx, perts, params):
        min_overlap = int(params.get("min_overlap", 10))
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # Build an essentiality matrix (genes x cell lines) from available knowledge.
        # gnomAD constraint gives one score per gene (not cell lines), so we treat
        # each available constraint metric as a "cell line"/dimension. If a richer
        # essentiality matrix is provided via knowledge, use it directly.
        ess_matrix = None
        gene_names = None

        # Try a dedicated essentiality knowledge source first.
        for kname in ("depmap_essentiality", "essentiality", "coessentiality"):
            try:
                kn = ctx.knowledge(kname)
            except Exception:
                kn = None
            if kn is None:
                continue
            if isinstance(kn, dict):
                genes = kn.get("genes")
                mat = kn.get("matrix")
                if genes is not None and mat is not None:
                    gene_names = list(genes)
                    ess_matrix = np.asarray(mat, dtype=float)
                    break
            elif isinstance(kn, (list, tuple)) and len(kn) > 0:
                # list of rows; attempt to interpret
                try:
                    ess_matrix = np.asarray(kn, dtype=float)
                except Exception:
                    ess_matrix = None
                if ess_matrix is not None:
                    break

        # Fallback: derive pseudo-essentiality profile from gnomAD constraint columns.
        if ess_matrix is None:
            try:
                gc = ctx.knowledge("gene_constraint")
            except Exception:
                gc = None
            if isinstance(gc, dict) and "genes" in gc:
                cols = gc.get("columns", [])
                gene_dict = gc.get("genes", {})
                # pick numeric constraint columns
                numeric_cols = []
                for ci, cname in enumerate(cols):
                    lc = str(cname).lower()
                    if any(tok in lc for tok in ("oe_lof", "pli", "lof", "oe_mis", "mis",
                                                 "syn", "oe_syn", "constraint")):
                        numeric_cols.append(ci)
                if not numeric_cols:
                    numeric_cols = list(range(len(cols)))
                gene_names = list(gene_dict.keys())
                ess_matrix = np.full((len(gene_names), len(numeric_cols)), np.nan)
                for gi, g in enumerate(gene_names):
                    vals = gene_dict.get(g)
                    if vals is None:
                        continue
                    for j, ci in enumerate(numeric_cols):
                        if ci < len(vals):
                            v = vals[ci]
                            if v is not None:
                                try:
                                    fv = float(v)
                                    if np.isfinite(fv):
                                        ess_matrix[gi, j] = fv
                                except (TypeError, ValueError):
                                    pass
                # drop all-NaN columns
                if ess_matrix.size:
                    keep = ~np.all(~np.isfinite(ess_matrix), axis=0)
                    ess_matrix = ess_matrix[:, keep]

        # Map gene names to ctx columns
        if ess_matrix is not None and gene_names is not None and ess_matrix.size:
            # rows: gene_names; build per-ctx-gene profile
            gene_to_row = {g: i for i, g in enumerate(gene_names)}
            profiles = np.full((n_genes, ess_matrix.shape[1]), np.nan)
            for gi, g in enumerate(ctx.genes):
                ri = gene_to_row.get(g)
                if ri is not None:
                    profiles[gi, :] = ess_matrix[ri, :]
            # Precompute rank-based correlation matrix lazily via scipy
            try:
                from scipy.stats import rankdata
            except Exception:
                rankdata = None

            if rankdata is not None:
                # For each perturbation, compute correlation between target profile and all genes
                cache = ctx.cache
                if "prof_ranked" not in cache:
                    # rank each gene's profile with NaN handling done pairwise later
                    cache["prof_ranked"] = None
                for i, p in enumerate(perts):
                    t_idx = ctx.target_indices(p)
                    if not t_idx:
                        continue
                    t = t_idx[0]
                    tv = profiles[t, :]
                    t_mask = np.isfinite(tv)
                    if t_mask.sum() < min_overlap:
                        continue
                    # For each gene g, pairwise-complete spearman
                    for g in range(n_genes):
                        if g == t:
                            out[i, g, 0] = 1.0
                            continue
                        gv = profiles[g, :]
                        mask = t_mask & np.isfinite(gv)
                        if mask.sum() < min_overlap:
                            continue
                        a = tv[mask]
                        b = gv[mask]
                        ra = rankdata(a)
                        rb = rankdata(b)
                        ra = ra - ra.mean()
                        rb = rb - rb.mean()
                        denom = np.sqrt((ra * ra).sum() * (rb * rb).sum())
                        if denom <= 0:
                            continue
                        out[i, g, 0] = float(np.dot(ra, rb) / denom)

        # Replace any non-finite with 0
        out[~np.isfinite(out)] = 0.0
        return out
