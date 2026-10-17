import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveResponseXTargetMembrane(Feature):
    name = "additive_response_x_target_membrane_e544"
    version = 1
    description = ("Product of additive_response and the mean membrane flag "
                   "(protein_annotation) of the perturbation's target genes.")
    rationale = ("Membrane-targeting perturbations may trigger extracellular "
                 "signaling or cell-cell communication that modulates the "
                 "additive transcriptional response.")
    inputs = ["control_cells", "train_delta", "knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        # additive_response baseline (sum over targets of each gene's delta)
        add = ctx.feature("additive_response", perts)
        if add.ndim == 3:
            add = add[:, :, 0]
        add = np.asarray(add, dtype=float)
        n_genes = ctx.n_genes
        n_perts = len(perts)

        # membrane flags from protein_annotation
        membrane = {}
        ann = ctx.knowledge("protein_annotation")
        if ann is not None:
            genes = ann.get("genes", {})
            cols = ann.get("columns", [])
            try:
                m_idx = cols.index("membrane")
            except ValueError:
                m_idx = None
            if m_idx is not None:
                for g, vals in genes.items():
                    if vals is None:
                        continue
                    v = vals[m_idx]
                    if v is not None:
                        membrane[g] = float(v)

        out = np.zeros((n_perts, n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue
            flags = [membrane.get(g, 0.0) for g in targets]
            m = float(np.mean(flags))
            out[i, :, 0] = add[i, :] * m

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
