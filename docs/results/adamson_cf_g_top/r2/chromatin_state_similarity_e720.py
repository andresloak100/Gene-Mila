import numpy as np
from genemila.features.api import Feature, register


@register
class ChromatinStateSimilarityE720(Feature):
    name = "chromatin_state_similarity_e720"
    version = 1
    description = (
        "Similarity between the perturbation target gene and each gene g based on "
        "promoter chromatin features (gc_promoter, cpg_oe_promoter, gc_cds, gc_utr3, "
        "nearest_tss_kb) from gene_annotation."
    )
    rationale = (
        "Genes with similar promoter chromatin state (e.g., CpG island, GC content) "
        "may respond similarly to perturbations of a target. Here we measure "
        "promoter-chromatin similarity between the target and each gene."
    )
    inputs = ["knowledge", "target_genes"]
    params = {"metric": "euclidean"}
    dim = 1

    # columns we use from gene_annotation
    _COLUMNS = ["gc_promoter", "cpg_oe_promoter", "gc_cds", "gc_utr3", "nearest_tss_kb"]

    def _build_matrix(self, ctx):
        cache = ctx.cache
        key = "_e720_chromatin_matrix"
        if key in cache:
            return cache[key]

        ann = ctx.knowledge("gene_annotation")
        n_genes = ctx.n_genes
        ncols = len(self._COLUMNS)

        mat = np.full((n_genes, ncols), np.nan, dtype=np.float64)

        if ann is not None:
            genes = ann.get("genes", {}) or {}
            columns = ann.get("columns", []) or []
            col_pos = {}
            for c in self._COLUMNS:
                if c in columns:
                    col_pos[c] = columns.index(c)

            for i, g in enumerate(ctx.genes):
                vals = genes.get(g)
                if vals is None:
                    continue
                for j, c in enumerate(self._COLUMNS):
                    cp = col_pos.get(c)
                    if cp is None:
                        continue
                    try:
                        v = vals[cp]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        mat[i, j] = fv

        # Standardize each column across genes that have data; leave NaN as NaN.
        means = np.zeros(ncols, dtype=np.float64)
        stds = np.ones(ncols, dtype=np.float64)
        for j in range(ncols):
            col = mat[:, j]
            mask = np.isfinite(col)
            if mask.sum() >= 2:
                m = col[mask].mean()
                s = col[mask].std()
                if s > 1e-12:
                    means[j] = m
                    stds[j] = s
                else:
                    means[j] = m
                    stds[j] = 1.0
            elif mask.sum() == 1:
                means[j] = col[mask][0]
                stds[j] = 1.0

        # Fill missing entries with column mean (0 after standardization).
        for j in range(ncols):
            col = mat[:, j]
            mask = ~np.isfinite(col)
            if mask.any():
                col[mask] = means[j]
                mat[:, j] = col

        mat = (mat - means) / stds

        cache[key] = mat
        return mat

    def compute(self, ctx, perts, params):
        metric = str(params.get("metric", "euclidean")).lower()
        mat = self._build_matrix(ctx)  # (n_genes, ncols), standardized
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=np.float64)

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                # no known target: leave zeros
                continue
            # Use the first target gene (single-gene targets in this dataset).
            ti = tgt_idx[0]
            if ti < 0 or ti >= n_genes:
                continue
            tv = mat[ti]  # (ncols,)
            diff = mat - tv[None, :]  # (n_genes, ncols)

            if metric == "euclidean":
                d = np.sqrt(np.sum(diff * diff, axis=1))
                # similarity in (0, 1]: 1 / (1 + d)
                sim = 1.0 / (1.0 + d)
            elif metric in ("cosine", "correlation"):
                t_norm = np.linalg.norm(tv)
                g_norms = np.linalg.norm(mat, axis=1)
                denom = g_norms * t_norm
                denom = np.where(denom > 1e-12, denom, 1.0)
                sim = (mat @ tv) / denom
                if metric == "cosine":
                    # map [-1,1] -> [0,1]
                    sim = 0.5 * (sim + 1.0)
            elif metric in ("manhattan", "l1"):
                d = np.sum(np.abs(diff), axis=1)
                sim = 1.0 / (1.0 + d)
            else:
                # default euclidean
                d = np.sqrt(np.sum(diff * diff, axis=1))
                sim = 1.0 / (1.0 + d)

            sim = np.where(np.isfinite(sim), sim, 0.0)
            out[i, :, 0] = sim

        return out
