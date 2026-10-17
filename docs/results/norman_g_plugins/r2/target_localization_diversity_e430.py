import numpy as np
from genemila.features.api import Feature, register

COMPARTMENTS = [
    "secreted", "membrane", "endoplasmic_reticulum", "golgi",
    "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome",
]


@register
class TargetLocalizationDiversity(Feature):
    name = "target_localization_diversity_e430"
    version = 1
    description = ("Number of distinct subcellular compartments among the "
                   "perturbation's target proteins (UniProt localization flags).")
    rationale = ("Targets in different compartments may trigger distinct downstream "
                 "pathways; diversity of localizations captures response heterogeneity.")
    inputs = ["target_genes", "knowledge"]
    params = {}
    dim = 1

    def _compartment_flags(self, ctx):
        cache = ctx.cache
        if "loc_div_flags" in cache:
            return cache["loc_div_flags"]

        ann = ctx.knowledge("protein_annotation")
        flags = {}
        if ann is not None:
            genes = ann.get("genes", {}) or {}
            columns = ann.get("columns", []) or []
            col_idx = {c: i for i, c in enumerate(columns)}
            comp_cols = [col_idx[c] for c in COMPARTMENTS if c in col_idx]
            for g, vals in genes.items():
                if vals is None:
                    continue
                v = np.asarray(vals, dtype=float)
                f = np.zeros(len(COMPARTMENTS), dtype=bool)
                for k, ci in enumerate(comp_cols):
                    if ci < v.shape[0] and np.isfinite(v[ci]) and v[ci] != 0:
                        f[COMPARTMENTS.index(COMPARTMENTS[k])] = True
                flags[g] = f
        cache["loc_div_flags"] = flags
        return flags

    def compute(self, ctx, perts, params):
        flags = self._compartment_flags(ctx)
        out = np.zeros((len(perts), ctx.n_genes, 1))
        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            union = np.zeros(len(COMPARTMENTS), dtype=bool)
            for g in targets:
                f = flags.get(g)
                if f is not None:
                    union |= f
            val = float(union.sum())
            out[i, :, 0] = val
        return out
