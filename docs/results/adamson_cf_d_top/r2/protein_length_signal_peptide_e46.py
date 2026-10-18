import numpy as np
from genemila.features.api import Feature, register


@register
class ProteinLengthSignalPeptideE46(Feature):
    name = "protein_length_signal_peptide_e46"
    version = 1
    description = "Standardized protein_length and signal_peptide_length per gene from protein_annotation."
    rationale = ("Longer proteins and those with signal peptides have different synthesis and "
                 "degradation rates, affecting how quickly mRNA levels change after perturbation.")
    inputs = ["protein_annotation"]
    params = {"columns": ["protein_length", "signal_peptide_length"]}
    dim = 2

    def compute(self, ctx, perts, params):
        columns = params.get("columns", ["protein_length", "signal_peptide_length"])
        n = ctx.n_genes
        out = np.zeros((len(perts), n, len(columns)), dtype=float)

        pa = ctx.knowledge("protein_annotation")
        if not pa:
            return out

        col_names = pa.get("columns", [])
        col_index = {c: i for i, c in enumerate(col_names)}
        genes = pa.get("genes", {}) or {}

        # Build per-gene value matrix aligned to ctx.genes
        mat = np.full((n, len(columns)), np.nan, dtype=float)
        for gi, g in enumerate(ctx.genes):
            vals = genes.get(g)
            if vals is None:
                continue
            for ci, cname in enumerate(columns):
                idx = col_index.get(cname)
                if idx is None or idx >= len(vals):
                    continue
                v = vals[idx]
                if v is None:
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv):
                    mat[gi, ci] = fv

        # Standardize each column across genes with observed values
        std_mat = np.zeros((n, len(columns)), dtype=float)
        for ci in range(len(columns)):
            col = mat[:, ci]
            mask = np.isfinite(col)
            if not np.any(mask):
                continue
            vals = col[mask]
            mu = vals.mean()
            sd = vals.std()
            if sd > 0 and np.isfinite(sd):
                std_mat[mask, ci] = (vals - mu) / sd
            else:
                std_mat[mask, ci] = 0.0

        std_mat = np.nan_to_num(std_mat, nan=0.0, posinf=0.0, neginf=0.0)
        out[:] = std_mat[np.newaxis, :, :]
        return out
