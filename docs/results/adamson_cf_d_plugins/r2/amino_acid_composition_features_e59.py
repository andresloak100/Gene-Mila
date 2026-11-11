import numpy as np
from genemila.features.api import Feature, register


@register
class AminoAcidCompositionFeaturesE59(Feature):
    name = "amino_acid_composition_features_e59"
    version = 1
    description = "Per-gene amino acid fractions from gene_annotation (aa_A..aa_Y), standardized."
    rationale = (
        "Amino acid composition determines protein stability and degradation rate, "
        "influencing the magnitude of expression change upon perturbation."
    )
    inputs = ["gene_annotation"]
    params = {}
    dim = 20

    _AA_COLS = [
        "aa_A", "aa_C", "aa_D", "aa_E", "aa_F", "aa_G", "aa_H", "aa_I",
        "aa_K", "aa_L", "aa_M", "aa_N", "aa_P", "aa_Q", "aa_R", "aa_S",
        "aa_T", "aa_V", "aa_W", "aa_Y",
    ]

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        n_aa = len(self._AA_COLS)
        out = np.zeros((len(perts), n_genes, n_aa), dtype=float)

        # Build per-gene matrix once (shared across perturbations).
        if "aa_matrix" in ctx.cache:
            mat = ctx.cache["aa_matrix"]
        else:
            ka = ctx.knowledge("gene_annotation")
            genes_tbl = ka.get("genes", {}) if ka else {}
            cols = ka.get("columns", []) if ka else []

            # Map each aa column to its index in the table's column list.
            col_idx = []
            for c in self._AA_COLS:
                if c in cols:
                    col_idx.append(cols.index(c))
                else:
                    col_idx.append(None)

            raw = np.full((n_genes, n_aa), np.nan, dtype=float)
            for gi, g in enumerate(ctx.genes):
                vals = genes_tbl.get(g)
                if vals is None:
                    continue
                for j, ci in enumerate(col_idx):
                    if ci is None:
                        continue
                    v = vals[ci]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        raw[gi, j] = fv

            # Standardize each column; fill missing with 0 after centering.
            mat = np.zeros_like(raw)
            for j in range(n_aa):
                col = raw[:, j]
                mask = np.isfinite(col)
                if mask.sum() >= 2:
                    mu = col[mask].mean()
                    sd = col[mask].std()
                    if sd > 1e-12:
                        mat[mask, j] = (col[mask] - mu) / sd
                    else:
                        mat[mask, j] = 0.0
                # missing entries remain 0 (mean after standardization)
            ctx.cache["aa_matrix"] = mat

        for i in range(len(perts)):
            out[i] = mat
        return out
