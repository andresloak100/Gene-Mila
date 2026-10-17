import numpy as np
from genemila.features.api import Feature, register


@register
class ChromatinStateSimilarityWithTarget(Feature):
    name = "chromatin_state_similarity_with_target_e634"
    version = 1
    description = (
        "Cosine similarity between a gene's chromatin-state proxy vector "
        "(promoter CpG/GC content and related annotation) and the mean vector "
        "of the perturbation's target genes."
    )
    rationale = (
        "Chromatin state influences gene regulation and may affect response to "
        "CRISPRa; genes sharing chromatin state with the targeted genes may "
        "respond more strongly. Without direct histone-mark data we use promoter "
        "GC/CpG content and related genomic annotation as a proxy vector."
    )
    inputs = ["control_mean", "knowledge"]
    params = {"use_proxy": True}
    dim = 1

    # Columns from gene_annotation we will use as the proxy vector.
    _ANNOT_COLS = [
        "gc_promoter",
        "cpg_oe_promoter",
        "gc_cds",
        "gc_utr3",
        "n_tss_within_100kb",
        "nearest_tss_kb",
        "gene_span_kb",
        "intron_length_kb",
        "n_transcripts",
        "n_exons",
    ]

    def _build_matrix(self, ctx, params):
        use_proxy = params.get("use_proxy", True)
        n = ctx.n_genes

        # Try to load gene_annotation knowledge for proxy features.
        ann = ctx.knowledge("gene_annotation")
        mat = None
        if ann is not None and isinstance(ann, dict) and "genes" in ann:
            genes_map = ann.get("genes", {})
            cols = ann.get("columns", None)
            if cols is None:
                cols = self._ANNOT_COLS
            # Determine which of our desired columns are available.
            col_idx = []
            for c in self._ANNOT_COLS:
                if c in cols:
                    col_idx.append((c, cols.index(c)))
            if col_idx:
                mat = np.zeros((n, len(col_idx)), dtype=np.float64)
                present = np.zeros((n, len(col_idx)), dtype=bool)
                for gi, g in enumerate(ctx.genes):
                    row = genes_map.get(g)
                    if row is None:
                        continue
                    for j, (_, ci) in enumerate(col_idx):
                        if ci < len(row) and row[ci] is not None:
                            try:
                                v = float(row[ci])
                            except (TypeError, ValueError):
                                continue
                            if np.isfinite(v):
                                mat[gi, j] = v
                                present[gi, j] = True
                # Fill missing entries with column means over present entries.
                for j in range(mat.shape[1]):
                    mask = present[:, j]
                    if mask.any():
                        col_mean = mat[mask, j].mean()
                        mat[~mask, j] = col_mean
                    else:
                        mat[:, j] = 0.0

        if mat is None or not use_proxy:
            # Fallback proxy: control expression profile summary per gene.
            # Use control_mean and control_std as a 2-d proxy; if use_proxy False
            # still provide a valid fallback so the feature is finite.
            cm = np.asarray(ctx.control_mean, dtype=np.float64)
            cs = np.asarray(ctx.control_std, dtype=np.float64)
            cm = np.where(np.isfinite(cm), cm, 0.0)
            cs = np.where(np.isfinite(cs), cs, 0.0)
            mat = np.stack([cm, cs], axis=1)

        # Standardise columns (z-score) so cosine similarity is meaningful,
        # then L2-normalise each row.
        mat = np.where(np.isfinite(mat), mat, 0.0)
        mu = mat.mean(axis=0, keepdims=True)
        sd = mat.std(axis=0, keepdims=True)
        sd = np.where(sd > 1e-8, sd, 1.0)
        z = (mat - mu) / sd
        norms = np.linalg.norm(z, axis=1, keepdims=True)
        norms = np.where(norms > 1e-8, norms, 1.0)
        z = z / norms
        return z

    def compute(self, ctx, perts, params):
        z = self._build_matrix(ctx, params)
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=np.float64)

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                # No measured target: similarity to zero vector -> 0.
                continue
            tgt_vec = z[tgt_idx, :].mean(axis=0)
            tnorm = np.linalg.norm(tgt_vec)
            if tnorm <= 1e-8:
                continue
            # z rows are already unit-norm; cosine = dot / tnorm.
            sims = z.dot(tgt_vec) / tnorm
            sims = np.where(np.isfinite(sims), sims, 0.0)
            out[i, :, 0] = sims

        return out
