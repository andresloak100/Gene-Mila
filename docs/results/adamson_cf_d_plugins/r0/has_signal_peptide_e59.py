import numpy as np
from genemila.features.api import Feature, register


@register
class HasSignalPeptideE59(Feature):
    name = "has_signal_peptide_e59"
    version = 1
    description = "Indicator that gene g's protein has a signal peptide (protein_annotation)."
    rationale = ("Signal peptide presence marks ER-targeted proteins, which may have distinct "
                 "mRNA regulation and response to perturbations.")
    inputs = ["protein_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1), dtype=float)

        ann = ctx.knowledge("protein_annotation")
        if not ann:
            return out

        genes = ann.get("genes", {}) or {}
        columns = ann.get("columns", []) or []
        try:
            col_idx = columns.index("has_signal_peptide")
        except ValueError:
            return out

        gene_vals = np.zeros(n, dtype=float)
        for j, g in enumerate(ctx.genes):
            vals = genes.get(g)
            if vals is None:
                continue
            try:
                v = vals[col_idx]
            except (IndexError, TypeError):
                continue
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv) and fv > 0:
                gene_vals[j] = 1.0

        out[:, :, 0] = gene_vals[None, :]
        return out
