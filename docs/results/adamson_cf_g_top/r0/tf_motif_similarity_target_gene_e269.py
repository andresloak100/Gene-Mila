import numpy as np
from genemila.features.api import Feature, register


@register
class TFMotifSimilarityTargetGene(Feature):
    name = "tf_motif_similarity_target_gene_e269"
    version = 1
    description = (
        "Cosine similarity between per-gene promoter motif occurrence vectors "
        "for the perturbation target gene and gene g."
    )
    rationale = (
        "Genes whose promoters share many transcription factor binding motifs with "
        "the target gene's promoter are likely co-regulated and thus more affected "
        "by perturbation of the target."
    )
    inputs = ["tf_motif_score_e179", "target_index"]
    params = {"motif_source": "tf_motif_score_e179"}
    dim = 1

    def _motif_matrix(self, ctx, params):
        """Return (n_genes, n_motifs) motif occurrence matrix, cached."""
        key = ("tf_motif_matrix", str(params.get("motif_source", "tf_motif_score_e179")))
        cache = ctx.cache
        if key in cache:
            return cache[key]

        mat = None
        try:
            # tf_motif_score_e179 outputs (n_perts, n_genes, dim) where dim is a
            # per-gene motif score. We reuse it as a per-gene motif vector. Since
            # the feature is defined per-perturbation but conceptually per-gene,
            # we compute it on all training perts and average to get a gene vector.
            train_perts = list(ctx.train_perts)
            if len(train_perts) > 0:
                arr = ctx.feature(params.get("motif_source", "tf_motif_score_e179"),
                                  train_perts)
                arr = np.asarray(arr, dtype=float)
                if arr.ndim == 3:
                    # average over perturbations -> (n_genes, dim)
                    gene_vec = arr.mean(axis=0)
                elif arr.ndim == 2:
                    gene_vec = arr
                else:
                    gene_vec = None
                if gene_vec is not None:
                    gene_vec = np.nan_to_num(gene_vec, nan=0.0, posinf=0.0, neginf=0.0)
                    # If dim == 1, the "vector" is scalar per gene. Cosine similarity
                    # of scalars is degenerate (sign only), so build a richer motif
                    # representation by combining this score with annotation-derived
                    # promoter features from gene_annotation when available.
                    if gene_vec.ndim == 2 and gene_vec.shape[1] == 1:
                        mat = self._build_annotation_motif_matrix(ctx, gene_vec[:, 0])
                    else:
                        mat = gene_vec
        except Exception:
            mat = None

        if mat is None:
            mat = self._build_annotation_motif_matrix(ctx, None)

        cache[key] = mat
        return mat

    def _build_annotation_motif_matrix(self, ctx, motif_score):
        """Build a per-gene motif/regulatory matrix.

        We use promoter-related annotation columns as a motif proxy:
        gc_promoter, cpg_oe_promoter, n_upstream_atg, n_tss_within_100kb,
        nearest_tss_kb, plus the tf_motif_score (if provided). These capture
        promoter architecture that correlates with shared TF motif content.
        """
        n_genes = ctx.n_genes
        cols = []
        ann = ctx.knowledge("gene_annotation")
        wanted = ["gc_promoter", "cpg_oe_promoter", "n_upstream_atg",
                  "n_tss_within_100kb", "nearest_tss_kb"]
        idx_map = {}
        if ann is not None:
            ann_cols = ann.get("columns", [])
            for w in wanted:
                if w in ann_cols:
                    idx_map[w] = ann_cols.index(w)

        base = np.zeros((n_genes, len(wanted)), dtype=float)
        if ann is not None and idx_map:
            genes_tbl = ann.get("genes", {})
            for gi, g in enumerate(ctx.genes):
                vals = genes_tbl.get(g)
                if vals is None:
                    continue
                for j, w in enumerate(wanted):
                    if w in idx_map:
                        v = vals[idx_map[w]]
                        if v is not None:
                            try:
                                base[gi, j] = float(v)
                            except (TypeError, ValueError):
                                base[gi, j] = 0.0
        base = np.nan_to_num(base, nan=0.0, posinf=0.0, neginf=0.0)

        # Standardise each column so cosine isn't dominated by scale.
        std = base.std(axis=0)
        std[std < 1e-8] = 1.0
        base = (base - base.mean(axis=0)) / std

        if motif_score is not None:
            ms = np.asarray(motif_score, dtype=float).reshape(-1)
            if ms.shape[0] == n_genes:
                ms = np.nan_to_num(ms, nan=0.0, posinf=0.0, neginf=0.0)
                s = ms.std()
                if s > 1e-8:
                    ms = (ms - ms.mean()) / s
                base = np.concatenate([base, ms[:, None]], axis=1)

        # Add a small positive offset so cosine is well-defined even for
        # near-zero vectors, and so that identical genes get similarity 1.
        base = base + 0.01
        return base

    def _cosine_rows(self, mat):
        norms = np.linalg.norm(mat, axis=1)
        norms[norms < 1e-12] = 1.0
        return mat / norms[:, None]

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        mat = self._motif_matrix(ctx, params)
        if mat.shape[0] != n_genes:
            # Fall back to zeros if shapes mismatch.
            return out

        normed = self._cosine_rows(mat)

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            # Average motif vector across target genes (usually one).
            tgt_vec = normed[tgt_idx, :].mean(axis=0)
            tn = np.linalg.norm(tgt_vec)
            if tn < 1e-12:
                continue
            tgt_vec = tgt_vec / tn
            sims = normed @ tgt_vec
            out[i, :, 0] = sims

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
