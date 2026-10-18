import numpy as np
from genemila.features.api import Feature, register


@register
class AACompositionGeneE125E137(Feature):
    name = "aa_composition_gene_e125_e137"
    version = 1
    description = (
        "Per-gene fractions of selected amino acids (H, C, R, K, D, E, N, Q, G) "
        "read from gene_annotation amino-acid columns; missing values imputed to 0."
    )
    rationale = (
        "Amino-acid composition reflects protein biophysical properties (stability, "
        "charge, flexibility) and may correlate with how gene expression responds to "
        "perturbations. These aa_* columns are otherwise unused."
    )
    inputs = ["knowledge:gene_annotation"]
    params = {"amino_acids": ["H", "C", "R", "K", "D", "E", "N", "Q", "G"]}
    dim = 9  # number of amino acid columns requested

    def compute(self, ctx, perts, params):
        amino_acids = params.get("amino_acids", ["H", "C", "R", "K", "D", "E", "N", "Q", "G"])
        # Normalise to uppercase single letters
        letters = [str(a).strip().upper() for a in amino_acids]
        dim = len(letters)

        out = np.zeros((len(perts), ctx.n_genes, dim), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is None:
            return out

        genes_table = ann.get("genes", {}) or {}
        columns = ann.get("columns", []) or []
        col_index = {c: i for i, c in enumerate(columns)}

        # Precompute per-gene vector of the requested amino-acid fractions
        gene_vec = np.zeros((ctx.n_genes, dim), dtype=float)
        for gi, g in enumerate(ctx.genes):
            vals = genes_table.get(g)
            if vals is None:
                continue
            for j, aa in enumerate(letters):
                col = "aa_" + aa
                if col in col_index:
                    ci = col_index[col]
                    if ci < len(vals):
                        v = vals[ci]
                        if v is not None:
                            try:
                                fv = float(v)
                            except (TypeError, ValueError):
                                fv = 0.0
                            if np.isfinite(fv):
                                gene_vec[gi, j] = fv

        # Same gene-level vector for every perturbation
        for i in range(len(perts)):
            out[i, :, :] = gene_vec

        # Ensure finiteness
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
