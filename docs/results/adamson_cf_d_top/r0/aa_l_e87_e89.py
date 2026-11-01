import numpy as np
from genemila.features.api import Feature, register


@register
class AALeucineFraction(Feature):
    name = "aa_l_e87_e89"
    version = 1
    description = "Fraction of leucine residues in the protein of gene g from gene_annotation."
    rationale = ("Leucine-rich proteins often participate in stable complexes, making their "
                 "expression less sensitive to perturbation.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        vals = np.full(n_genes, np.nan, dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            columns = ann.get("columns", [])
            genes = ann.get("genes", {}) or {}
            try:
                col_idx = columns.index("aa_L")
            except ValueError:
                col_idx = None
            if col_idx is not None:
                for g, row in genes.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None or row is None:
                        continue
                    try:
                        v = row[col_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        v = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(v):
                        vals[gi] = v

        # Fill missing with the mean of available values (0 if none).
        finite = np.isfinite(vals)
        if finite.any():
            fill = float(vals[finite].mean())
        else:
            fill = 0.0
        vals[~finite] = fill

        out = np.empty((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = vals[None, :]
        return out
