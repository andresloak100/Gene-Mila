import numpy as np
from genemila.features.api import Feature, register

COMPARTMENTS = [
    "secreted", "membrane", "endoplasmic_reticulum", "golgi",
    "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome",
]


@register
class TargetLocalizationInteractionE403(Feature):
    name = "target_localization_interaction_e403"
    version = 1
    description = (
        "For each (p,g): number of shared subcellular compartments between the "
        "perturbation target protein and gene g's protein."
    )
    rationale = (
        "Perturbing a gene whose protein localizes to a compartment may "
        "preferentially affect genes whose products localize to the same "
        "compartment, capturing compartment-specific regulatory effects."
    )
    inputs = ["protein_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        pa = ctx.knowledge("protein_annotation")
        if pa is None:
            return out

        genes = pa.get("genes", {})
        columns = pa.get("columns", [])
        col_index = {c: i for i, c in enumerate(columns)}

        comp_cols = [col_index[c] for c in COMPARTMENTS if c in col_index]
        if not comp_cols:
            return out

        # Build (n_genes, n_compartments) binary flag matrix aligned to ctx.genes.
        flag_mat = np.zeros((n_genes, len(comp_cols)), dtype=float)
        for gi, gene in enumerate(ctx.genes):
            vals = genes.get(gene)
            if vals is None:
                continue
            for ci, col in enumerate(comp_cols):
                v = vals[col] if col < len(vals) else None
                if v is not None:
                    try:
                        flag_mat[gi, ci] = 1.0 if float(v) > 0 else 0.0
                    except (TypeError, ValueError):
                        flag_mat[gi, ci] = 0.0

        for i, p in enumerate(perts):
            tidx = ctx.target_indices(p)
            if not tidx:
                continue
            # Target compartment vector: any target gene with the flag.
            tflags = flag_mat[tidx].max(axis=0)  # (n_compartments,)
            # Shared compartments per gene g: sum_c target_c * gene_c
            out[i, :, 0] = flag_mat.dot(tflags)

        out[~np.isfinite(out)] = 0.0
        return out
