import numpy as np
from genemila.features.api import Feature, register

_COMPARTMENTS = [
    "secreted", "membrane", "endoplasmic_reticulum", "golgi",
    "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome",
]


@register
class TargetCompartmentDiversity(Feature):
    name = "target_compartment_diversity_e503"
    version = 1
    description = "Number of distinct subcellular compartments (protein_annotation flags) among a perturbation's target genes."
    rationale = "Targets in different compartments may trigger distinct pathways, modulating response magnitude."
    inputs = ["protein_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("protein_annotation")
        cols = ann.get("columns", []) if ann else []
        genes_tbl = ann.get("genes", {}) if ann else {}

        # column index for each compartment flag
        flag_idx = {}
        for comp in _COMPARTMENTS:
            if comp in cols:
                flag_idx[comp] = cols.index(comp)

        # precompute compartment set per gene symbol
        comp_sets = {}
        for sym, vals in genes_tbl.items():
            if not vals:
                continue
            s = set()
            for comp, ci in flag_idx.items():
                try:
                    v = vals[ci]
                except (IndexError, TypeError):
                    continue
                if v is not None:
                    try:
                        if float(v) != 0.0:
                            s.add(comp)
                    except (TypeError, ValueError):
                        pass
            if s:
                comp_sets[sym] = s

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            union = set()
            for g in tg:
                s = comp_sets.get(g)
                if s:
                    union |= s
            out[i, :, 0] = float(len(union))
        return out
