import numpy as np
from genemila.features.api import Feature, register


@register
class SignalPeptideLengthE89(Feature):
    name = "signal_peptide_length_e89"
    version = 1
    description = "Continuous feature: length of the signal peptide for gene g's protein, from protein_annotation."
    rationale = (
        "Longer signal peptides may increase sensitivity to perturbations affecting protein "
        "translocation and ER stress, leading to larger expression changes."
    )
    inputs = ["protein_annotation"]
    params = {"column": "signal_peptide_length"}
    dim = 1

    def compute(self, ctx, perts, params):
        col = params.get("column", "signal_peptide_length")
        n_genes = ctx.n_genes
        base = np.zeros(n_genes, dtype=float)

        ann = ctx.knowledge("protein_annotation")
        if ann is not None:
            columns = ann.get("columns", [])
            genes = ann.get("genes", {}) or {}
            if col in columns:
                idx = columns.index(col)
                for g, vals in genes.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None or vals is None:
                        continue
                    if idx >= len(vals):
                        continue
                    v = vals[idx]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        base[gi] = fv

        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = base[None, :]
        return out
