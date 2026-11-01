import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGeneSharedCompartmentE23(Feature):
    name = "target_gene_shared_compartment_e23"
    version = 1
    description = ("Binary indicator: 1 if the target of perturbation p and gene g share at "
                   "least one subcellular localization flag from protein_annotation, else 0.")
    rationale = ("Proteins in the same subcellular compartment are more likely to be "
                 "functionally connected, so perturbing one affects the expression of "
                 "co-localized genes more strongly.")
    inputs = ["protein_annotation"]
    params = {}
    dim = 1

    # Compartment flag columns in protein_annotation
    COMPARTMENTS = [
        "secreted", "membrane", "endoplasmic_reticulum", "golgi",
        "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome",
    ]

    def _get_compartment_matrix(self, ctx):
        cache = ctx.cache
        key = "_shared_compartment_e23_matrix"
        if key in cache:
            return cache[key]

        n = ctx.n_genes
        mat = np.zeros((n, len(self.COMPARTMENTS)), dtype=np.float32)

        ann = ctx.knowledge("protein_annotation")
        if ann is not None:
            genes = ann.get("genes", {}) or {}
            columns = ann.get("columns", []) or []
            # Map compartment name -> column index in the annotation values
            col_idx = {}
            for c in self.COMPARTMENTS:
                if c in columns:
                    col_idx[c] = columns.index(c)

            for g, gi in ctx.gene_index.items():
                vals = genes.get(g)
                if vals is None:
                    continue
                for c, ci in col_idx.items():
                    v = vals[ci]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv) and fv > 0:
                        mat[gi, self.COMPARTMENTS.index(c)] = 1.0

        cache[key] = mat
        return mat

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1), dtype=np.float32)

        comp = self._get_compartment_matrix(ctx)

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            # Union of compartment flags across all targets of p
            tgt_flags = comp[tgt_idx].max(axis=0)  # (n_comp,)
            if tgt_flags.sum() == 0:
                continue
            # Shared compartment: gene g has any flag that target also has
            shared = (comp * tgt_flags[None, :]).sum(axis=1) > 0
            out[i, :, 0] = shared.astype(np.float32)

        return out
