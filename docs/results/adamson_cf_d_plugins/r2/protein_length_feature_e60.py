import numpy as np
from genemila.features.api import Feature, register


@register
class ProteinLengthFeatureE60(Feature):
    name = "protein_length_feature_e60"
    version = 1
    description = "Per-gene protein_length from protein_annotation, standardized."
    rationale = (
        "Protein length affects synthesis cost and degradation rate, modulating "
        "the expression response to perturbations."
    )
    inputs = ["knowledge:protein_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        vals = np.full(n_genes, np.nan, dtype=float)

        ann = ctx.knowledge("protein_annotation")
        if ann is not None:
            genes_tbl = ann.get("genes", {}) if isinstance(ann, dict) else {}
            cols = ann.get("columns", []) if isinstance(ann, dict) else []
            try:
                col_idx = list(cols).index("protein_length")
            except (ValueError, TypeError):
                col_idx = None
            if col_idx is not None:
                for g, gi in ctx.gene_index.items():
                    row = genes_tbl.get(g)
                    if row is None:
                        continue
                    try:
                        v = row[col_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        vals[gi] = fv

        # Standardize using finite observed values
        finite = np.isfinite(vals)
        if finite.any():
            mu = vals[finite].mean()
            sd = vals[finite].std()
            if not np.isfinite(sd) or sd <= 0:
                sd = 1.0
        else:
            mu = 0.0
            sd = 1.0

        z = (vals - mu) / sd
        # Missing values -> 0 (mean of standardized scale)
        z[~np.isfinite(z)] = 0.0

        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = z[np.newaxis, :]
        return out
