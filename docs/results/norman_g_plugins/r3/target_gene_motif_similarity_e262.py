import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGeneMotifSimilarityE262(Feature):
    name = "target_gene_motif_similarity_e262"
    version = 1
    description = ("Cosine similarity between promoter motif profiles of the perturbation "
                   "target gene(s) and gene g, averaged over the targets for pairs.")
    rationale = ("Genes with similar regulatory motif profiles may respond similarly to "
                 "perturbations of transcription factors, capturing indirect regulatory effects.")
    inputs = ["gene_annotation", "control_mean"]
    params = {"default": "cosine"}
    dim = 1

    def _motif_matrix(self, ctx):
        """Build a (n_genes, n_features) promoter motif profile matrix.

        Primary source: gene_annotation promoter-related columns (gc_promoter,
        cpg_oe_promoter, n_tss_within_100kb, n_upstream_atg) plus a control-expression
        derived regulatory proxy. Falls back to control_mean if annotation unavailable.
        """
        cache = ctx.cache
        if "motif_matrix_e262" in cache:
            return cache["motif_matrix_e262"]

        n = ctx.n_genes
        feats = []

        ann = ctx.knowledge("gene_annotation")
        if ann is not None and isinstance(ann, dict) and "genes" in ann:
            cols = ann.get("columns", [])
            gene_vals = ann.get("genes", {})
            # pick promoter / regulatory columns
            wanted = ["gc_promoter", "cpg_oe_promoter", "n_tss_within_100kb",
                      "n_upstream_atg", "gc_cds", "gc_utr3"]
            col_idx = {c: i for i, c in enumerate(cols)}
            for w in wanted:
                if w in col_idx:
                    j = col_idx[w]
                    vec = np.full(n, np.nan, dtype=float)
                    for gi, g in enumerate(ctx.genes):
                        vals = gene_vals.get(g)
                        if vals is not None and j < len(vals) and vals[j] is not None:
                            try:
                                vec[gi] = float(vals[j])
                            except (TypeError, ValueError):
                                pass
                    feats.append(vec)

        # expression-derived regulatory proxy (always available)
        cm = np.asarray(ctx.control_mean, dtype=float)
        feats.append(cm)

        if len(feats) == 0:
            mat = cm.reshape(n, 1).copy()
        else:
            mat = np.column_stack(feats)

        # impute NaNs with column mean, then z-score columns
        for j in range(mat.shape[1]):
            col = mat[:, j]
            mask = ~np.isfinite(col)
            if mask.any():
                finite = col[~mask]
                fill = finite.mean() if finite.size else 0.0
                col[mask] = fill
                mat[:, j] = col
            std = col.std()
            if std > 1e-12:
                mat[:, j] = (col - col.mean()) / std
            else:
                mat[:, j] = 0.0

        cache["motif_matrix_e262"] = mat
        return mat

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        mat = self._motif_matrix(ctx)  # (n, k)

        # precompute row norms
        norms = np.linalg.norm(mat, axis=1)
        norms[norms < 1e-12] = 1e-12
        norm_mat = mat / norms[:, None]

        out = np.zeros((len(perts), n, 1), dtype=float)

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            tgt_idx = [t for t in tgt_idx if 0 <= t < n]
            if not tgt_idx:
                continue
            # mean motif vector over targets
            tgt_vec = norm_mat[tgt_idx].mean(axis=0)
            tn = np.linalg.norm(tgt_vec)
            if tn < 1e-12:
                continue
            tgt_vec = tgt_vec / tn
            # cosine similarity to every gene
            sims = norm_mat @ tgt_vec  # (n,)
            out[i, :, 0] = sims

        # ensure finite
        out[~np.isfinite(out)] = 0.0
        return out
