import numpy as np
from genemila.features.api import Feature, register


@register
class SignalPeptideLength(Feature):
    name = "signal_peptide_length_e183_e185"
    version = 1
    description = "Length of the signal peptide for gene g from protein_annotation."
    rationale = ("Longer signal peptides may indicate stronger ER targeting, affecting "
                 "protein processing and gene expression feedback.")
    inputs = ["protein_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        out = np.zeros((n_perts, ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("protein_annotation")
        if ann is None:
            return out

        genes = ann.get("genes", {})
        cols = ann.get("columns", [])
        try:
            idx = cols.index("signal_peptide_length")
        except ValueError:
            return out

        # Build per-gene value vector aligned to ctx.genes
        vals = np.zeros(ctx.n_genes, dtype=float)
        for g, ci in ctx.gene_index.items():
            entry = genes.get(g)
            if entry is None:
                continue
            try:
                v = entry[idx]
            except (IndexError, TypeError):
                continue
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv):
                vals[ci] = fv

        out[:, :, 0] = vals[None, :]
        return out
