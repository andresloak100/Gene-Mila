import numpy as np
from genemila.features.api import Feature, register


@register
class GeneAnnotationRandomProjectionE51(Feature):
    name = "gene_annotation_random_projection_e51"
    version = 1
    description = "20 random projections of standardized unread gene_annotation numeric columns."
    rationale = ("Gene annotation contains many correlated structural properties; a random "
                 "projection summarizes them into a compact representation capturing latent "
                 "regulatory constraints.")
    inputs = ["gene_annotation"]
    params = {"n_components": 20, "seed": 42}
    dim = 20

    _COLUMNS = [
        "gene_span_kb", "n_transcripts", "n_exons", "transcript_length",
        "cds_length", "utr5_length", "utr3_length", "intron_length_kb",
        "gc_cds", "gc_utr3", "gc_promoter", "cpg_oe_promoter",
        "n_upstream_atg", "nearest_tss_kb", "n_tss_within_100kb",
    ]

    def _build(self, ctx, params):
        n_comp = int(params.get("n_components", 20))
        seed = int(params.get("seed", 42))
        key = ("garp_e51", n_comp, seed)
        cache = ctx.cache
        if key in cache:
            return cache[key]

        n_genes = ctx.n_genes

        ann = ctx.knowledge("gene_annotation")
        genes_map = {}
        columns = None
        if isinstance(ann, dict):
            genes_map = ann.get("genes", {}) or {}
            columns = ann.get("columns", None)

        if columns is not None:
            col_index = {c: i for i, c in enumerate(columns)}
            use_cols = [c for c in self._COLUMNS if c in col_index]
            use_idx = [col_index[c] for c in use_cols]
        else:
            use_cols = list(self._COLUMNS)
            use_idx = None

        n_cols = len(use_cols)
        raw = np.full((n_genes, n_cols), np.nan, dtype=np.float64)

        idx_list = use_idx if use_idx is not None else list(range(n_cols))
        for gi, g in enumerate(ctx.genes):
            vals = genes_map.get(g, None)
            if vals is None:
                continue
            try:
                arr = np.asarray(vals, dtype=object)
            except Exception:
                continue
            for j, ci in enumerate(idx_list):
                if ci < len(arr):
                    v = arr[ci]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        raw[gi, j] = fv

        col_mean = np.nanmean(raw, axis=0) if n_cols > 0 else np.zeros(0)
        col_std = np.nanstd(raw, axis=0) if n_cols > 0 else np.zeros(0)
        col_mean = np.where(np.isfinite(col_mean), col_mean, 0.0)
        col_std = np.where(np.isfinite(col_std) & (col_std > 1e-12), col_std, 1.0)

        if n_cols == 0:
            feats = np.zeros((n_genes, n_comp), dtype=np.float64)
            cache[key] = feats
            return feats

        Z = (raw - col_mean) / col_std
        Z = np.where(np.isfinite(Z), Z, 0.0)

        rng = np.random.RandomState(seed)
        proj = rng.randn(n_cols, n_comp) / np.sqrt(max(n_cols, 1))
        feats = Z @ proj

        f_std = feats.std(axis=0)
        f_std = np.where(f_std > 1e-12, f_std, 1.0)
        feats = feats / f_std

        feats = np.where(np.isfinite(feats), feats, 0.0).astype(np.float64)
        cache[key] = feats
        return feats

    def compute(self, ctx, perts, params):
        feats = self._build(ctx, params)  # (n_genes, n_comp)
        n_comp = feats.shape[1]
        n = len(perts)
        out = np.empty((n, ctx.n_genes, n_comp), dtype=np.float64)
        for i in range(n):
            out[i] = feats
        return out
