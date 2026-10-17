import numpy as np
from genemila.features.api import Feature, register

_COMPARTMENTS = [
    "secreted", "membrane", "endoplasmic_reticulum", "golgi",
    "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome",
]


@register
class TargetCompartmentXGeneCompartment(Feature):
    name = "target_compartment_x_gene_compartment_e2_e304"
    version = 1
    description = ("Indicator that the target gene and gene g share at least one "
                   "protein compartment annotation from protein_annotation flags.")
    rationale = ("Compartment-specific perturbations may preferentially affect genes "
                 "encoding proteins in the same compartment.")
    inputs = ["protein_annotation", "targets"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        pa = ctx.knowledge("protein_annotation")
        if not pa:
            return out
        genes_tbl = pa.get("genes", {})
        cols = pa.get("columns", [])
        # locate compartment flag columns
        col_idx = {}
        for c in _COMPARTMENTS:
            if c in cols:
                col_idx[c] = cols.index(c)
        if not col_idx:
            return out

        # Build gene x compartment boolean matrix
        comp_mat = np.zeros((n_genes, len(col_idx)), dtype=bool)
        comp_names = list(col_idx.keys())
        for gi, g in enumerate(ctx.genes):
            vals = genes_tbl.get(g)
            if vals is None:
                continue
            for ci, cname in enumerate(comp_names):
                v = vals[col_idx[cname]]
                if v is not None:
                    try:
                        if float(v) > 0.5:
                            comp_mat[gi, ci] = True
                    except (TypeError, ValueError):
                        pass

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            # union of compartments across target genes
            tgt_comp = comp_mat[tgt_idx, :].any(axis=0)  # (n_comp,)
            if not tgt_comp.any():
                continue
            shared = comp_mat[:, :] & tgt_comp[None, :]
            out[i, :, 0] = shared.any(axis=1).astype(float)

        return out
