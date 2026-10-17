import numpy as np
from genemila.features.api import Feature, register


@register
class RandomProjectionStaticFeaturesE424(Feature):
    name = "random_projection_static_features_e424"
    version = 1
    description = ("Concatenate static gene features (annotation, constraint, protein) for gene g "
                   "and for the perturbation target, then project to a fixed low dimension with a "
                   "deterministic random matrix.")
    rationale = ("Static gene properties capture latent structure (localisation, constraint, "
                 "sequence composition) that may correlate with perturbation response magnitude; "
                 "a random projection compresses them into a compact, leakage-free embedding.")
    inputs = ["knowledge"]
    params = {"n_components": 20, "seed": 42}
    dim = 20

    def _build_feature_matrix(self, ctx):
        # Returns (feature_matrix (n_genes, n_static), gene_to_row mapping via ctx.gene_index order)
        genes = ctx.genes
        n = len(genes)
        cols = []

        # ---- gene_annotation ----
        ann = ctx.knowledge("gene_annotation")
        ann_cols = None
        ann_genes = {}
        if isinstance(ann, dict):
            ann_genes = ann.get("genes", {}) or {}
            ann_cols = ann.get("columns", None)
        # Determine numeric width from annotation columns (excluding aa_ columns handled separately)
        # We'll build a fixed numeric layout dynamically.
        aa_cols = ["aa_" + c for c in "ACDEFGHIKLMNPQRSTVWY"]
        base_cols = None
        if ann_cols is not None:
            base_cols = [c for c in ann_cols if not c.startswith("aa_")]
        else:
            base_cols = ["gene_span_kb", "n_transcripts", "n_exons", "transcript_length",
                         "cds_length", "utr5_length", "utr3_length", "intron_length_kb",
                         "gc_cds", "gc_utr3", "gc_promoter", "cpg_oe_promoter",
                         "n_upstream_atg", "nearest_tss_kb", "n_tss_within_100kb"]

        def ann_vec(g):
            vals = ann_genes.get(g, None) if ann_genes else None
            out = []
            if vals is None:
                out = [np.nan] * (len(base_cols) + len(aa_cols))
                return out
            # vals is a list in order of ann columns; map by name if possible
            if ann_cols is not None and len(vals) == len(ann_cols):
                d = dict(zip(ann_cols, vals))
                for c in base_cols:
                    out.append(d.get(c, np.nan))
                for c in aa_cols:
                    out.append(d.get(c, np.nan))
            else:
                out = [np.nan] * (len(base_cols) + len(aa_cols))
            return out

        ann_mat = np.array([ann_vec(g) for g in genes], dtype=float)
        cols.append(ann_mat)

        # ---- gene_constraint ----
        cons = ctx.knowledge("gene_constraint")
        cons_genes = {}
        cons_cols = None
        if isinstance(cons, dict):
            cons_genes = cons.get("genes", {}) or {}
            cons_cols = cons.get("columns", None)
        if cons_cols is None:
            cons_cols = ["oe_lof", "oe_lof_lower", "oe_lof_upper", "pLI", "lof_z",
                         "exp_lof", "obs_lof", "oe_mis", "pRec", "exp_mis", "obs_mis",
                         "oe_syn", "exp_syn", "obs_syn", "syn_z", "mis_z", "lof_z"]
        cons_mat = np.full((n, len(cons_cols)), np.nan, dtype=float)
        for i, g in enumerate(genes):
            v = cons_genes.get(g, None) if cons_genes else None
            if v is None:
                continue
            if len(v) == len(cons_cols):
                for j, val in enumerate(v):
                    try:
                        cons_mat[i, j] = float(val)
                    except (TypeError, ValueError):
                        cons_mat[i, j] = np.nan
            else:
                # best effort: fill up to available
                for j in range(min(len(v), len(cons_cols))):
                    try:
                        cons_mat[i, j] = float(v[j])
                    except (TypeError, ValueError):
                        cons_mat[i, j] = np.nan
        cols.append(cons_mat)

        # ---- protein_annotation ----
        prot = ctx.knowledge("protein_annotation")
        prot_genes = {}
        prot_cols = None
        if isinstance(prot, dict):
            prot_genes = prot.get("genes", {}) or {}
            prot_cols = prot.get("columns", None)
        if prot_cols is None:
            prot_cols = ["protein_length", "has_signal_peptide", "signal_peptide_length",
                         "n_transmembrane", "secreted", "membrane", "endoplasmic_reticulum",
                         "golgi", "mitochondrion", "nucleus", "cytoplasm", "lysosome",
                         "peroxisome"]
        prot_mat = np.full((n, len(prot_cols)), np.nan, dtype=float)
        for i, g in enumerate(genes):
            v = prot_genes.get(g, None) if prot_genes else None
            if v is None:
                continue
            for j in range(min(len(v), len(prot_cols))):
                try:
                    prot_mat[i, j] = float(v[j])
                except (TypeError, ValueError):
                    prot_mat[i, j] = np.nan
        cols.append(prot_mat)

        # ---- bidirectional / neighbours derived simple flags (static, no response) ----
        bid = ctx.knowledge("bidirectional")
        nei = ctx.knowledge("neighbours")
        bid_flag = np.zeros((n, 1), dtype=float)
        nbr_count = np.zeros((n, 1), dtype=float)
        nbr_mean_dist = np.full((n, 1), np.nan, dtype=float)
        if isinstance(bid, dict):
            bgenes = bid.get("genes", {}) or bid
            if isinstance(bgenes, dict):
                for i, g in enumerate(genes):
                    if g in bgenes:
                        bid_flag[i, 0] = 1.0
        if isinstance(nei, dict):
            ngenes = nei.get("genes", {}) or nei
            if isinstance(ngenes, dict):
                for i, g in enumerate(genes):
                    lst = ngenes.get(g, None)
                    if lst:
                        nbr_count[i, 0] = float(len(lst))
                        dists = []
                        for item in lst:
                            try:
                                dists.append(abs(float(item[1])))
                            except (TypeError, ValueError, IndexError):
                                pass
                        if dists:
                            nbr_mean_dist[i, 0] = float(np.mean(dists))
        cols.append(bid_flag)
        cols.append(nbr_count)
        cols.append(nbr_mean_dist)

        mat = np.concatenate(cols, axis=1)
        # sanitize: replace nan/inf with column means (or 0)
        mat = np.where(np.isfinite(mat), mat, np.nan)
        col_mean = np.nanmean(mat, axis=0)
        col_mean = np.where(np.isfinite(col_mean), col_mean, 0.0)
        inds = np.where(~np.isfinite(mat))
        mat[inds] = np.take(col_mean, inds[1])
        return mat

    def compute(self, ctx, perts, params):
        n_components = int(params.get("n_components", 20))
        seed = int(params.get("seed", 42))
        n = ctx.n_genes

        if "static_feat_matrix" in ctx.cache:
            feat_mat = ctx.cache["static_feat_matrix"]
        else:
            feat_mat = self._build_feature_matrix(ctx)
            ctx.cache["static_feat_matrix"] = feat_mat

        n_static = feat_mat.shape[1]
        # Combined vector: [static(g), static(target)] -> 2*n_static
        d_in = 2 * n_static
        rng = np.random.RandomState(seed)
        # Standard normal random projection scaled
        R = rng.normal(0.0, 1.0 / np.sqrt(n_components), size=(d_in, n_components))

        out = np.zeros((len(perts), n, n_components), dtype=float)
        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if len(tgt_idx) == 0:
                # no target measured -> use zero target vector
                tgt_vec = np.zeros(n_static, dtype=float)
            else:
                tgt_vec = feat_mat[tgt_idx[0]]
            # combined per gene: (n, d_in)
            combined = np.concatenate([feat_mat, np.tile(tgt_vec, (n, 1))], axis=1)
            proj = combined.dot(R)
            out[i] = proj
        return out
