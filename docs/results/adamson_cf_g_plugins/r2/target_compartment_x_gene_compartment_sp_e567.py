import numpy as np
from genemila.features.api import Feature, register

COMPARTMENTS = [
    "secreted", "membrane", "endoplasmic_reticulum", "golgi",
    "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome",
]


@register
class TargetCompartmentXGeneCompartmentSpE567(Feature):
    name = "target_compartment_x_gene_compartment_sp_e567"
    version = 1
    description = (
        "Product of indicator that target protein localizes to compartment C and "
        "indicator that gene g's protein localizes to the same compartment C, "
        "for each of 9 compartments (one-hot expansion)."
    )
    rationale = (
        "Perturbing a target localized to a specific compartment affects genes whose "
        "products localize to the same compartment, reflecting organelle-specific "
        "stress responses."
    )
    inputs = ["protein_annotation"]
    params = {"expand_compartments": True}
    dim = len(COMPARTMENTS)

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        n_genes = ctx.n_genes
        dim = len(COMPARTMENTS)
        out = np.zeros((n_perts, n_genes, dim), dtype=float)

        ann = ctx.knowledge("protein_annotation")
        if not ann or "genes" not in ann or "columns" not in ann:
            return out

        cols = list(ann["columns"])
        genes_data = ann["genes"]
        # locate compartment column indices
        comp_idx = []
        for c in COMPARTMENTS:
            if c in cols:
                comp_idx.append(cols.index(c))
            else:
                comp_idx.append(None)

        # build gene x compartment flag matrix aligned to ctx.genes
        gene_flags = np.zeros((n_genes, dim), dtype=float)
        gene_index = ctx.gene_index
        for sym, vals in genes_data.items():
            gi = gene_index.get(sym)
            if gi is None:
                continue
            if not isinstance(vals, (list, tuple)):
                continue
            for k, ci in enumerate(comp_idx):
                if ci is None or ci >= len(vals):
                    continue
                v = vals[ci]
                if v is None:
                    continue
                try:
                    gene_flags[gi, k] = 1.0 if float(v) != 0.0 else 0.0
                except (TypeError, ValueError):
                    pass

        # build target x compartment flag matrix
        for i, p in enumerate(perts):
            target_genes = ctx.target_genes(p)
            if not target_genes:
                continue
            tflags = np.zeros(dim, dtype=float)
            for tg in target_genes:
                vals = genes_data.get(tg)
                if vals is None or not isinstance(vals, (list, tuple)):
                    continue
                for k, ci in enumerate(comp_idx):
                    if ci is None or ci >= len(vals):
                        continue
                    v = vals[ci]
                    if v is None:
                        continue
                    try:
                        if float(v) != 0.0:
                            tflags[k] = 1.0
                    except (TypeError, ValueError):
                        pass
            # outer product: (dim,) x (n_genes, dim) -> sum per compartment
            out[i] = tflags[None, :] * gene_flags

        return out
