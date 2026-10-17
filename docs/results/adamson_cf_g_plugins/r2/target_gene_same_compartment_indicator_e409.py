import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGeneSameCompartmentIndicator(Feature):
    name = "target_gene_same_compartment_indicator_e409"
    version = 1
    description = "Indicator that target and gene g share at least one protein compartment annotation."
    rationale = ("Compartment-specific processes may be co-regulated; perturbing a target in a "
                 "compartment may preferentially affect genes encoding proteins in the same compartment.")
    inputs = ["protein_annotation", "target_indices"]
    params = {"compartments": ["nucleus", "cytoplasm", "membrane", "secreted",
                               "endoplasmic_reticulum", "golgi", "mitochondrion",
                               "lysosome", "peroxisome"]}
    dim = 1

    def compute(self, ctx, perts, params):
        comps = list(params.get("compartments", self.params["compartments"]))
        ann = ctx.knowledge("protein_annotation")
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        # Build (n_genes, n_comps) binary compartment matrix
        comp_mat = np.zeros((n_genes, len(comps)), dtype=np.float32)
        if ann is not None:
            columns = ann.get("columns", [])
            col_idx = {}
            for j, c in enumerate(columns):
                col_idx[c] = j
            genes_dict = ann.get("genes", {}) or {}
            # determine indices for compartment flags
            flag_cols = []
            for c in comps:
                if c in col_idx:
                    flag_cols.append((col_idx[c], c))
                else:
                    flag_cols.append((None, c))
            for gi, g in enumerate(ctx.genes):
                vals = genes_dict.get(g)
                if vals is None:
                    continue
                for ci, (col, cname) in enumerate(flag_cols):
                    if col is None:
                        continue
                    try:
                        v = vals[col]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        if float(v) > 0:
                            comp_mat[gi, ci] = 1.0
                    except (TypeError, ValueError):
                        continue

        has_any = comp_mat.sum(axis=1) > 0  # (n_genes,)

        for i, p in enumerate(perts):
            tgt = ctx.target_indices(p)
            if not tgt:
                continue
            # OR over target indices of compartment flags
            tgt_flags = comp_mat[tgt, :].max(axis=0)  # (n_comps,)
            if tgt_flags.sum() == 0:
                continue
            # shared compartment: intersection nonempty
            shared = (comp_mat * tgt_flags[None, :]).sum(axis=1) > 0
            out[i, :, 0] = shared.astype(np.float32)

        return out
