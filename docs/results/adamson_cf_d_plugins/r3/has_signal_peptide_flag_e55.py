import numpy as np
from genemila.features.api import Feature, register

@register
class HasSignalPeptideFlagE55(Feature):
    name = "has_signal_peptide_flag_e55"
    version = 1
    description = "Binary feature: 1 if gene g's protein has a signal peptide, else 0."
    rationale = ("Secretory/ER-targeted genes may be co-regulated under perturbation of "
                 "ER or secretory pathways.")
    inputs = ["protein_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        flag = np.zeros(n_genes, dtype=float)

        pa = ctx.knowledge("protein_annotation")
        if pa is not None:
            cols = pa.get("columns", [])
            genes = pa.get("genes", {})
            try:
                idx = cols.index("has_signal_peptide")
            except (ValueError, AttributeError):
                idx = None
            if idx is not None and isinstance(genes, dict):
                for g, vals in genes.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None or vals is None:
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
                    if np.isfinite(fv) and fv > 0.5:
                        flag[gi] = 1.0

        out = np.broadcast_to(flag[None, :, None], (len(perts), n_genes, 1)).copy()
        return out
