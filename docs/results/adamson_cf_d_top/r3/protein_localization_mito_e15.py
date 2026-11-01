import numpy as np
from genemila.features.api import Feature, register

@register
class ProteinLocalizationMitoE15(Feature):
    name = "protein_localization_mito_e15"
    version = 1
    description = "Binary: 1 if gene g's protein is annotated as mitochondrial, else 0."
    rationale = ("Mitochondrial proteins participate in compartment-specific stress "
                 "responses that may be perturbed by many targets, giving distinct "
                 "expression changes.")
    inputs = ["protein_annotation"]
    params = {"compartment": "mitochondrion"}
    dim = 1

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        col = np.zeros(n, dtype=float)

        ann = ctx.knowledge("protein_annotation")
        compartment = params.get("compartment", "mitochondrion")
        if ann is not None:
            columns = ann.get("columns", [])
            genes_tbl = ann.get("genes", {})
            if compartment in columns:
                idx = columns.index(compartment)
                for g, vals in genes_tbl.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None or vals is None:
                        continue
                    if idx < len(vals):
                        v = vals[idx]
                        if v is not None and v == 1:
                            col[gi] = 1.0

        out = np.zeros((len(perts), n, 1), dtype=float)
        out[:, :, 0] = col[None, :]
        return out
