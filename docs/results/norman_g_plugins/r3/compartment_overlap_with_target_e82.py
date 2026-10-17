import numpy as np
from genemila.features.api import Feature, register

_COMPARTMENTS = [
    "secreted", "membrane", "endoplasmic_reticulum", "golgi",
    "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome",
]


@register
class CompartmentOverlapWithTargetE82(Feature):
    name = "compartment_overlap_with_target_e82"
    version = 1
    description = ("For gene g and perturbation p, count the number of subcellular "
                   "compartments shared between g and any target gene of p.")
    rationale = ("Perturbing a gene may affect proteins in the same subcellular "
                 "compartment through shared pathways or physical interactions.")
    inputs = ["protein_annotation", "target_genes"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        ann = ctx.knowledge("protein_annotation")
        if not ann or "genes" not in ann:
            return out

        cols = ann.get("columns", [])
        col_idx = {c: i for i, c in enumerate(cols)}
        present = [c for c in _COMPARTMENTS if c in col_idx]
        if not present:
            return out

        # Build gene x compartment binary matrix.
        mat = np.zeros((n_genes, len(present)), dtype=float)
        table = ann["genes"]
        for gi, g in enumerate(ctx.genes):
            vals = table.get(g)
            if vals is None:
                continue
            for ci, c in enumerate(present):
                v = vals[col_idx[c]]
                if v is not None:
                    try:
                        mat[gi, ci] = 1.0 if float(v) > 0 else 0.0
                    except (TypeError, ValueError):
                        pass

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            if not tgenes:
                continue
            tvec = np.zeros(len(present), dtype=float)
            any_t = False
            for tg in tgenes:
                gi = ctx.gene_index.get(tg)
                if gi is None:
                    continue
                tvec = np.maximum(tvec, mat[gi])
                any_t = True
            if not any_t:
                continue
            out[i, :, 0] = mat @ tvec

        return out
