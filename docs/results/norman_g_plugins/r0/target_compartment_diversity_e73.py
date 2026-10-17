import numpy as np
from genemila.features.api import Feature, register

# localization flag columns in protein_annotation
LOC_COLS = [
    "secreted", "membrane", "endoplasmic_reticulum", "golgi",
    "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome",
]


@register
class TargetCompartmentDiversityE73(Feature):
    name = "target_compartment_diversity_e73"
    version = 1
    description = (
        "Number of distinct UniProt localization flags across the target genes "
        "of each perturbation (union of flag sets)."
    )
    rationale = (
        "Targets in different cellular compartments engage distinct pathways; "
        "the diversity of compartments hit by a perturbation may predict how "
        "broad or synergistic its downstream response is."
    )
    inputs = ["protein_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))

        ann = ctx.knowledge("protein_annotation")
        if ann is None:
            return out

        genes_tbl = ann.get("genes", {}) or {}
        columns = list(ann.get("columns", []) or [])

        # map localization flag name -> column index
        col_idx = {}
        for name in LOC_COLS:
            if name in columns:
                col_idx[name] = columns.index(name)
        if not col_idx:
            return out

        # cache per-gene flag sets
        flag_cache = {}

        def gene_flags(g):
            if g in flag_cache:
                return flag_cache[g]
            vals = genes_tbl.get(g)
            if vals is None:
                flag_cache[g] = frozenset()
                return flag_cache[g]
            s = set()
            for name, ci in col_idx.items():
                try:
                    v = vals[ci]
                except (IndexError, TypeError):
                    continue
                if v is None:
                    continue
                try:
                    if float(v) != 0.0:
                        s.add(name)
                except (TypeError, ValueError):
                    continue
            fs = frozenset(s)
            flag_cache[g] = fs
            return fs

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            union = set()
            for g in tg:
                union |= gene_flags(g)
            out[i, :, 0] = float(len(union))

        return out
