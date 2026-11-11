import numpy as np
from genemila.features.api import Feature, register


@register
class TranscriptUtrFeaturesE35(Feature):
    name = "transcript_utr_features_e35"
    version = 1
    description = "Standardized per-gene n_transcripts, utr5_length, utr3_length from gene_annotation."
    rationale = ("Transcript complexity and UTR lengths affect mRNA stability and translation, "
                 "modulating response to perturbations.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 3

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, self.dim), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        cols = ["n_transcripts", "utr5_length", "utr3_length"]

        mat = np.full((n_genes, self.dim), np.nan, dtype=float)

        if ann is not None:
            col_names = ann.get("columns", [])
            genes_tbl = ann.get("genes", {}) or {}
            col_idx = []
            for c in cols:
                try:
                    col_idx.append(col_names.index(c))
                except ValueError:
                    col_idx.append(-1)

            for gi, g in enumerate(ctx.genes):
                vals = genes_tbl.get(g)
                if vals is None:
                    continue
                for k, ci in enumerate(col_idx):
                    if ci < 0 or ci >= len(vals):
                        continue
                    v = vals[ci]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        mat[gi, k] = fv

        # Standardize each column across genes, treating missing as 0 after centering.
        for k in range(self.dim):
            col = mat[:, k]
            valid = np.isfinite(col)
            if valid.sum() >= 2:
                mu = col[valid].mean()
                sd = col[valid].std()
            elif valid.sum() == 1:
                mu = col[valid].mean()
                sd = 0.0
            else:
                mu = 0.0
                sd = 0.0
            filled = np.where(valid, col, mu)
            if sd > 1e-12:
                mat[:, k] = (filled - mu) / sd
            else:
                mat[:, k] = 0.0

        mat = np.nan_to_num(mat, nan=0.0, posinf=0.0, neginf=0.0)
        out[:, :, :] = mat[None, :, :]
        return out
