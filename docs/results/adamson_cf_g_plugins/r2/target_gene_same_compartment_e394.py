import numpy as np
from genemila.features.api import Feature, register

_COMPARTMENTS = [
    "secreted", "membrane", "endoplasmic_reticulum", "golgi",
    "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome",
]


@register
class TargetGeneSameCompartmentE394(Feature):
    name = "target_gene_same_compartment_e394"
    version = 1
    description = ("Indicator (0/1) that the perturbation target t and gene g share "
                   "at least one cellular compartment annotation from protein_annotation.")
    rationale = ("Compartment-specific perturbations often disrupt local functions; "
                 "shared localization increases likelihood of direct or indirect interaction.")
    inputs = ["protein_annotation", "target_indices"]
    params = {}
    dim = 1

    def _compartment_matrix(self, ctx):
        cache = ctx.cache
        key = "_e394_comp_matrix"
        if key in cache:
            return cache[key]

        ann = ctx.knowledge("protein_annotation")
        n_genes = ctx.n_genes
        mat = np.zeros((n_genes, len(_COMPARTMENTS)), dtype=np.float32)

        if ann is not None:
            genes_tbl = ann.get("genes", {}) or {}
            columns = ann.get("columns", []) or []
            # Map compartment name -> column index
            col_idx = {}
            for c in _COMPARTMENTS:
                if c in columns:
                    col_idx[c] = columns.index(c)
            if col_idx:
                for g, col in ctx.gene_index.items():
                    vals = genes_tbl.get(g)
                    if vals is None:
                        continue
                    for c, ci in col_idx.items():
                        try:
                            v = vals[ci]
                        except (IndexError, TypeError):
                            continue
                        if v is None:
                            continue
                        try:
                            if float(v) > 0.5:
                                mat[col, _COMPARTMENTS.index(c)] = 1.0
                        except (TypeError, ValueError):
                            continue
        cache[key] = mat
        return mat

    def compute(self, ctx, perts, params):
        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1), dtype=np.float32)
        mat = self._compartment_matrix(ctx)

        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if not t_idx:
                continue
            t_flags = np.any(mat[t_idx, :] > 0.5, axis=0)  # (n_comp,)
            if not t_flags.any():
                continue
            # genes that share at least one compartment with target
            shared = np.any(mat[:, t_flags] > 0.5, axis=1)
            out[i, :, 0] = shared.astype(np.float32)

        return out
