import numpy as np
from genemila.features.api import Feature, register

@register
class HasSignalPeptideE70(Feature):
    name = "has_signal_peptide_e70"
    version = 1
    description = "Indicator that gene g's protein has a signal peptide (protein_annotation)."
    rationale = ("Signal peptide targets protein to ER; ER-associated degradation may "
                 "buffer mRNA changes, attenuating expression responses.")
    inputs = ["protein_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        vec = np.zeros(n_genes, dtype=float)

        ann = ctx.knowledge("protein_annotation")
        if ann is not None:
            cols = ann.get("columns", [])
            genes = ann.get("genes", {})
            try:
                idx = cols.index("has_signal_peptide")
            except ValueError:
                idx = None
            if idx is not None:
                for g, ci in ctx.gene_index.items():
                    vals = genes.get(g)
                    if vals is None:
                        continue
                    try:
                        v = vals[idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        vec[ci] = fv

        out = np.broadcast_to(vec[None, :, None], (len(perts), n_genes, 1)).copy()
        out[~np.isfinite(out)] = 0.0
        return out
