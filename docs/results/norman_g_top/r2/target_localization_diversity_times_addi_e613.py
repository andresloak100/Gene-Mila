import numpy as np
from genemila.features.api import Feature, register

COMPARTMENTS = [
    "secreted", "membrane", "endoplasmic_reticulum", "golgi",
    "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome",
]


@register
class TargetLocalizationDiversityTimesAdditive(Feature):
    name = "target_localization_diversity_times_addi_e613"
    version = 1
    description = ("Number of distinct subcellular compartments (protein_annotation flags) "
                   "among p's target genes, multiplied by additive_response.")
    rationale = ("Perturbations whose target proteins localize to many compartments may "
                 "have broader downstream effects, scaling the additive baseline.")
    inputs = ["control_cells", "train_delta", "knowledge"]
    params = {}
    dim = 1

    def _compartment_sets(self, ctx):
        cache = ctx.cache
        if "loc_div_comp" in cache:
            return cache["loc_div_comp"]
        ann = ctx.knowledge("protein_annotation")
        sets = {}
        if ann is not None:
            genes = ann.get("genes", {})
            cols = ann.get("columns", [])
            col_idx = {c: i for i, c in enumerate(cols)}
            comp_cols = [col_idx[c] for c in COMPARTMENTS if c in col_idx]
            for g, vals in genes.items():
                if vals is None:
                    continue
                comps = set()
                for ci, cname in zip(comp_cols, [c for c in COMPARTMENTS if c in col_idx]):
                    try:
                        v = vals[ci]
                    except (IndexError, TypeError):
                        continue
                    if v is not None and v == v and v > 0:
                        comps.add(cname)
                sets[g] = comps
        cache["loc_div_comp"] = sets
        return sets

    def compute(self, ctx, perts, params):
        comp_sets = self._compartment_sets(ctx)
        out = np.zeros((len(perts), ctx.n_genes, 1))
        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            union = set()
            for g in tg:
                union |= comp_sets.get(g, set())
            diversity = float(len(union))
            _, d = ctx.train_delta(exclude=p)
            add = d.sum(axis=0)
            out[i, :, 0] = diversity * add
        return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
