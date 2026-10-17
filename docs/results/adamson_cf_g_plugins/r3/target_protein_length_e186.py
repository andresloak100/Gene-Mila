import numpy as np
from genemila.features.api import Feature, register

@register
class TargetProteinLengthE186(Feature):
    name = "target_protein_length_e186"
    version = 1
    description = "Length of the protein encoded by the perturbation target gene."
    rationale = "Longer proteins may have more functional domains and larger regulatory impact."
    inputs = ["protein_annotation", "target_genes"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))

        ann = ctx.knowledge("protein_annotation")
        genes_ann = {}
        length_idx = 0
        if ann is not None and "genes" in ann:
            genes_ann = ann["genes"]
            cols = ann.get("columns", [])
            try:
                length_idx = cols.index("protein_length")
            except (ValueError, AttributeError):
                length_idx = 0

        # Collect all target protein lengths to compute a median fill
        target_lengths = []
        for p in perts:
            for tg in ctx.target_genes(p):
                val = None
                rec = genes_ann.get(tg)
                if rec is not None:
                    try:
                        v = rec[length_idx]
                        if v is not None:
                            fv = float(v)
                            if np.isfinite(fv):
                                val = fv
                    except (IndexError, TypeError, ValueError):
                        val = None
                target_lengths.append(val)

        finite_vals = [v for v in target_lengths if v is not None]
        fill = float(np.median(finite_vals)) if finite_vals else 0.0

        for i, p in enumerate(perts):
            tgs = ctx.target_genes(p)
            length = fill
            for tg in tgs:
                rec = genes_ann.get(tg)
                if rec is not None:
                    try:
                        v = rec[length_idx]
                        if v is not None:
                            fv = float(v)
                            if np.isfinite(fv):
                                length = fv
                                break
                    except (IndexError, TypeError, ValueError):
                        pass
            out[i, :, 0] = length

        return out
