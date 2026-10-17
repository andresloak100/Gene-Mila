import numpy as np
from genemila.features.api import Feature, register

_COMPARTMENTS = [
    "secreted", "membrane", "endoplasmic_reticulum", "golgi",
    "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome",
]


@register
class TargetCompartmentCountTimesAdditive(Feature):
    name = "target_compartment_count_times_additive__e470"
    version = 1
    description = ("Mean number of subcellular compartment flags of p's target proteins, "
                   "multiplied by additive_response.")
    rationale = ("Protein localization influences CRISPRa efficacy and downstream effects; "
                 "multi-localization complexity may modulate the additive response.")
    inputs = ["protein_annotation", "additive_response"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        ann = ctx.knowledge("protein_annotation")
        cols = None
        genes_map = {}
        if isinstance(ann, dict):
            cols = ann.get("columns")
            genes_map = ann.get("genes") or {}

        # Determine indices of compartment columns
        comp_idx = []
        if cols is not None:
            col_index = {c: i for i, c in enumerate(cols)}
            for c in _COMPARTMENTS:
                if c in col_index:
                    comp_idx.append(col_index[c])

        # Precompute per-gene compartment count
        gene_count = np.zeros(n_genes, dtype=float)
        if comp_idx:
            for g, gi in ctx.gene_index.items():
                vals = genes_map.get(g)
                if vals is None:
                    continue
                cnt = 0.0
                for ci in comp_idx:
                    try:
                        v = vals[ci]
                    except (IndexError, TypeError):
                        v = None
                    if v is not None:
                        try:
                            cnt += float(v)
                        except (TypeError, ValueError):
                            pass
                gene_count[gi] = cnt

        # additive_response feature
        add = ctx.feature("additive_response", perts, None)
        add = np.asarray(add, dtype=float)
        if add.ndim == 3:
            add2 = add[:, :, 0]
        elif add.ndim == 2:
            add2 = add
        else:
            add2 = np.broadcast_to(add.reshape(-1, 1), (len(perts), n_genes))

        for i, p in enumerate(perts):
            tgt = ctx.target_indices(p)
            if tgt:
                mean_cnt = float(np.mean(gene_count[tgt]))
            else:
                mean_cnt = 0.0
            out[i, :, 0] = mean_cnt * add2[i, :]

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
