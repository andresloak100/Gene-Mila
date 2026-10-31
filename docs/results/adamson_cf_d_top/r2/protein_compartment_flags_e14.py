import numpy as np
from genemila.features.api import Feature, register

@register
class ProteinCompartmentFlagsE14(Feature):
    name = "protein_compartment_flags_e14"
    version = 1
    description = "Binary protein localization compartment flags per gene from protein_annotation."
    rationale = ("Perturbations may trigger compartment-specific stress responses; genes encoding "
                 "proteins in the affected compartment may show coordinated expression changes.")
    inputs = ["protein_annotation"]
    params = {}
    dim = 7

    _COMPARTMENTS = ["mitochondrion", "nucleus", "endoplasmic_reticulum", "golgi",
                     "cytoplasm", "secreted", "membrane"]

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, self.dim), dtype=float)

        pa = ctx.knowledge("protein_annotation")
        if not pa:
            return out

        cols = pa.get("columns", [])
        genes_table = pa.get("genes", {})
        if not genes_table or not cols:
            return out

        col_idx = {c: i for i, c in enumerate(cols)}

        # Precompute per-gene flag vector once (shared across perturbations)
        key = "protein_compartment_flags_e14_matrix"
        mat = ctx.cache.get(key)
        if mat is None:
            mat = np.zeros((n_genes, self.dim), dtype=float)
            for g, col in ctx.gene_index.items():
                vals = genes_table.get(g)
                if vals is None:
                    continue
                for j, comp in enumerate(self._COMPARTMENTS):
                    ci = col_idx.get(comp)
                    if ci is None:
                        continue
                    v = vals[ci]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv) and fv != 0.0:
                        mat[col, j] = 1.0
            ctx.cache[key] = mat

        for i in range(len(perts)):
            out[i] = mat
        return out
