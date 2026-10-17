import numpy as np
from genemila.features.api import Feature, register


@register
class SharedTFMotifSimilarityE175(Feature):
    name = "shared_tf_motif_similarity_e175"
    version = 1
    description = (
        "Similarity between target gene t and gene g based on overlap of predicted "
        "transcription factor binding motifs in their promoters (from promoter GC "
        "content, CpG islands and upstream ATG/TSS density proxies)."
    )
    rationale = (
        "Genes sharing promoter regulatory logic (similar GC/CpG content and TSS "
        "architecture) may be co-regulated by the same TFs; perturbing a regulator "
        "should therefore affect genes with similar promoter features."
    )
    inputs = ["control_mean", "knowledge"]
    params = {"promoter_window": 1000, "motif_database": "jaspar_core"}
    dim = 1

    def _promoter_features(self, ctx):
        """Build a per-gene promoter feature matrix from gene_annotation knowledge."""
        cache = ctx.cache
        if "_e175_promoter_feats" in cache:
            return cache["_e175_promoter_feats"]

        n = ctx.n_genes
        # Default: neutral feature vector (all zeros -> cosine sim 0).
        feats = np.zeros((n, 6), dtype=np.float64)

        ann = ctx.knowledge("gene_annotation")
        if ann is not None and isinstance(ann, dict):
            genes = ann.get("genes", {}) or {}
            columns = ann.get("columns", []) or []
            col_idx = {c: i for i, c in enumerate(columns)}

            # Columns we can use as promoter "motif" proxies.
            use_cols = [
                "gc_promoter",
                "cpg_oe_promoter",
                "n_upstream_atg",
                "n_tss_within_100kb",
                "gc_cds",
                "gc_utr3",
            ]
            idxs = [col_idx[c] for c in use_cols if c in col_idx]
            names = [c for c in use_cols if c in col_idx]

            if idxs:
                mat = np.full((n, len(idxs)), np.nan, dtype=np.float64)
                for g, gi in ctx.gene_index.items():
                    vals = genes.get(g)
                    if not vals:
                        continue
                    row = []
                    ok = True
                    for j in idxs:
                        v = vals[j] if j < len(vals) else None
                        if v is None:
                            ok = False
                            break
                        try:
                            row.append(float(v))
                        except (TypeError, ValueError):
                            ok = False
                            break
                    if ok:
                        mat[gi, :] = row

                # Fill missing with column median (or 0 if all missing).
                for k in range(mat.shape[1]):
                    col = mat[:, k]
                    finite = np.isfinite(col)
                    if finite.any():
                        med = float(np.median(col[finite]))
                    else:
                        med = 0.0
                    col[~finite] = med
                    mat[:, k] = col

                # Standardise each column.
                mu = mat.mean(axis=0)
                sd = mat.std(axis=0)
                sd[sd < 1e-8] = 1.0
                mat = (mat - mu) / sd

                # Pad/truncate to 6 columns.
                feats[:, : mat.shape[1]] = mat[:, :6]
                if mat.shape[1] < 6:
                    feats[:, mat.shape[1]:] = 0.0

        # L2-normalise rows so cosine similarity = dot product.
        norms = np.linalg.norm(feats, axis=1, keepdims=True)
        norms[norms < 1e-8] = 1.0
        feats = feats / norms

        cache["_e175_promoter_feats"] = feats
        return feats

    def compute(self, ctx, perts, params):
        feats = self._promoter_features(ctx)
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=np.float64)

        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if not t_idx:
                continue
            # Use first measured target gene.
            t = t_idx[0]
            # Cosine similarity between target promoter features and all genes.
            sim = feats @ feats[t]
            # Keep in [0, 1] for a "similarity" feature; clip small negatives.
            sim = np.clip(sim, 0.0, 1.0)
            out[i, :, 0] = sim

        # Ensure finite.
        out[~np.isfinite(out)] = 0.0
        return out
