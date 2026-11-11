import numpy as np
from genemila.features.api import Feature, register

@register
class TargetAaKFractionE228(Feature):
    name = "target_aa_k_fraction_e228"
    version = 1
    description = "Fraction of lysine residues in the protein of the target gene of perturbation p."
    rationale = ("Lysine-rich proteins are heavily regulated by post-translational modifications, "
                 "so their perturbation may cause widespread expression changes.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        ann = ctx.knowledge("gene_annotation")
        genes = ann.get("genes", {}) if ann else {}
        columns = ann.get("columns", []) if ann else []

        try:
            k_idx = columns.index("aa_K")
        except ValueError:
            k_idx = None

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            val = 0.0
            if k_idx is not None:
                for t in ctx.target_genes(p):
                    row = genes.get(t)
                    if row is None:
                        continue
                    try:
                        v = row[k_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is not None:
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv):
                            val = fv
                            break
            out[i, :, 0] = val

        return out
