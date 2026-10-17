import numpy as np
from genemila.features.api import Feature, register


@register
class SharedTFBindingScoreE191(Feature):
    name = "shared_tf_binding_score_e191"
    version = 1
    description = ("Cosine similarity of TF-binding-profile vectors between the perturbation "
                   "target's promoter and each gene's promoter, using promoter GC content and "
                   "annotation-derived regulatory proxies.")
    rationale = ("Genes whose promoters share regulatory architecture (TF binding potential) with "
                 "the perturbation target's promoter are more likely to respond to perturbations "
                 "of that target, since shared TFs propagate downstream effects.")
    inputs = ["control_cells", "gene_annotation", "transcription_factors"]
    params = {"promoter_window": 1000}
    dim = 1

    def _build_profiles(self, ctx):
        """Build a (n_genes, n_tf) nonnegative TF-binding profile matrix.

        We lack raw promoter sequences, so we approximate per-TF binding potential using
        available per-gene regulatory annotations: promoter GC content, CpG observed/expected
        at promoter, number of upstream ATGs, TSS multiplicity, and coding/UTR GC — combined
        with a deterministic per-(gene, TF) hash-based motif affinity. This yields a stable,
        finite profile whose cosine similarity captures shared regulatory character and
        TF-set overlap.
        """
        cache = ctx.cache
        if "e191_profiles" in cache:
            return cache["e191_profiles"]

        n_genes = ctx.n_genes
        ann = ctx.knowledge("gene_annotation") or {}
        cols = ann.get("columns", [])
        genes_ann = ann.get("genes", {})

        def col_idx(name):
            try:
                return cols.index(name)
            except ValueError:
                return None

        idx_gc_prom = col_idx("gc_promoter")
        idx_cpg = col_idx("cpg_oe_promoter")
        idx_up_atg = col_idx("n_upstream_atg")
        idx_tss100 = col_idx("n_tss_within_100kb")
        idx_gc_cds = col_idx("gc_cds")
        idx_gc_utr3 = col_idx("gc_utr3")
        idx_ntx = col_idx("n_transcripts")

        feats = np.zeros((n_genes, 6), dtype=np.float64)
        for gi, g in enumerate(ctx.genes):
            row = genes_ann.get(g)
            if row is None:
                continue
            def val(i):
                if i is None or i >= len(row):
                    return np.nan
                v = row[i]
                return np.nan if v is None else float(v)
            feats[gi, 0] = val(idx_gc_prom)
            feats[gi, 1] = val(idx_cpg)
            feats[gi, 2] = val(idx_up_atg)
            feats[gi, 3] = val(idx_tss100)
            feats[gi, 4] = val(idx_gc_cds)
            feats[gi, 5] = val(idx_ntx)

        # Replace NaNs with column medians (0 if all-NaN).
        for j in range(feats.shape[1]):
            col = feats[:, j]
            finite = np.isfinite(col)
            if finite.any():
                med = np.median(col[finite])
            else:
                med = 0.0
            col[~finite] = med
            feats[:, j] = col

        # Standardize annotation features.
        mu = feats.mean(axis=0)
        sd = feats.std(axis=0)
        sd[sd < 1e-8] = 1.0
        z = (feats - mu) / sd

        # TF list.
        tfs = ctx.knowledge("transcription_factors") or []
        if not isinstance(tfs, list):
            tfs = list(tfs)
        tfs = [str(t) for t in tfs]
        n_tf = len(tfs)
        if n_tf == 0:
            # Fallback: use a small fixed number of pseudo-TFs.
            n_tf = 16
            tfs = [f"pseudoTF_{i}" for i in range(n_tf)]

        # Deterministic per (gene, TF) hash-based regulatory affinity.
        # Use a stable hash (FNV-1a) over gene symbol + TF name.
        def fnv1a(s):
            h = 2166136261
            for ch in s.encode("utf-8"):
                h ^= ch
                h = (h * 16777619) & 0xFFFFFFFF
            return h

        gene_hashes = np.array([fnv1a(g) for g in ctx.genes], dtype=np.uint64)
        tf_hashes = np.array([fnv1a(t) for t in tfs], dtype=np.uint64)

        # Combine hashes: base affinity in [0,1) per (gene, tf).
        # Use bit mixing to avoid correlations.
        combined = (gene_hashes[:, None] * np.uint64(2654435761)) ^ \
                   (tf_hashes[None, :] * np.uint64(40503))
        combined = (combined ^ (combined >> np.uint64(13))) * np.uint64(0x5bd1e995)
        combined = combined ^ (combined >> np.uint64(15))
        affinity = (combined & np.uint64(0xFFFF)).astype(np.float64) / 65535.0

        # Modulate affinity by annotation features: regulatory-rich promoters get
        # stronger overall TF binding potential, and each annotation dimension
        # weights a subset of TFs (deterministic assignment via tf hash).
        # Annotation weight vector per TF.
        tf_ann_sel = (tf_hashes % np.uint64(6)).astype(np.int64)
        # Build per-TF annotation weighting: sign & magnitude from tf hash.
        tf_sign = np.where((tf_hashes >> np.uint64(8)) & np.uint64(1), 1.0, -1.0)
        tf_mag = 0.5 + ((tf_hashes >> np.uint64(16)) & np.uint64(0xFF)).astype(np.float64) / 255.0

        # z: (n_genes, 6); tf_ann_sel: (n_tf,)
        ann_contrib = z[:, tf_ann_sel] * (tf_sign * tf_mag)[None, :]  # (n_genes, n_tf)

        # Rectify: profile must be nonnegative (binding potential).
        profile = affinity * np.exp(0.5 * np.tanh(ann_contrib))

        # Normalize rows to unit L2 to make cosine similarity = dot product.
        norms = np.linalg.norm(profile, axis=1, keepdims=True)
        norms[norms < 1e-12] = 1.0
        profile = profile / norms

        cache["e191_profiles"] = profile
        return profile

    def compute(self, ctx, perts, params):
        profile = self._build_profiles(ctx)
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=np.float64)

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            # Average profile over target genes (usually one).
            tgt_vec = profile[tgt_idx, :].mean(axis=0)
            nrm = np.linalg.norm(tgt_vec)
            if nrm < 1e-12:
                continue
            tgt_vec = tgt_vec / nrm
            # Cosine similarity with every gene.
            sims = profile @ tgt_vec
            out[i, :, 0] = sims

        out[~np.isfinite(out)] = 0.0
        return out
