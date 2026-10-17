import numpy as np
from genemila.features.api import Feature, register


@register
class ProteinCompartmentFlagE82(Feature):
    name = "protein_compartment_flag_e82"
    version = 1
    description = (
        "Binary indicator (per gene) of whether the gene's protein is annotated "
        "in a chosen subcellular compartment from protein_annotation."
    )
    rationale = (
        "Protein localization flags are static gene properties; compartment "
        "membership may correlate with distinct perturbation response programs."
    )
    inputs = ["knowledge:protein_annotation"]
    params = {"compartment": "nucleus"}
    dim = 1

    # compartment name -> column index in the protein_annotation value vector
    _COMPARTMENTS = {
        "secreted": 2,
        "membrane": 3,
        "endoplasmic_reticulum": 4,
        "golgi": 5,
        "mitochondrion": 6,
        "nucleus": 7,
        "cytoplasm": 8,
        "lysosome": 9,
        "peroxisome": 10,
    }

    def compute(self, ctx, perts, params):
        comp = params.get("compartment", "nucleus")
        col = self._COMPARTMENTS.get(comp, 7)

        ann = ctx.knowledge("protein_annotation")
        flag = np.zeros(ctx.n_genes, dtype=float)

        if ann is not None:
            genes_tbl = ann.get("genes", {}) or {}
            for i, g in enumerate(ctx.genes):
                vals = genes_tbl.get(g)
                if vals is None:
                    continue
                try:
                    v = vals[col]
                except (IndexError, TypeError):
                    continue
                if v is None:
                    continue
                try:
                    flag[i] = 1.0 if float(v) > 0 else 0.0
                except (TypeError, ValueError):
                    continue

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        out[:, :, 0] = flag[None, :]
        return out
