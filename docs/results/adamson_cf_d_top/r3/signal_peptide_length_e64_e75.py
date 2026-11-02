import numpy as np
from genemila.features.api import Feature, register


@register
class SignalPeptideLength(Feature):
    name = "signal_peptide_length_e64_e75"
    version = 1
    description = "Length of signal peptide for gene g from protein_annotation."
    rationale = (
        "Longer signal peptides may be less efficiently cleaved or more sensitive to ER "
        "stress, altering protein maturation and downstream expression."
    )
    inputs = ["protein_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        values = np.zeros(n_genes, dtype=float)

        ann = ctx.knowledge("protein_annotation")
        if ann is not None:
            genes = ann.get("genes", {})
            cols = ann.get("columns", [])
            try:
                sp_idx = cols.index("signal_peptide_length")
            except ValueError:
                sp_idx = None

            if sp_idx is not None:
                for g, vals in genes.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None:
                        continue
                    if vals is None:
                        continue
                    v = vals[sp_idx]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        values[gi] = fv

        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = values[None, :]
        out[~np.isfinite(out)] = 0.0
        return out
