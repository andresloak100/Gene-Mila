import numpy as np
from genemila.features.api import Feature, register

@register
class TargetLocalizationDiversityE277(Feature):
    name = "target_localization_diversity_e277"
    version = 1
    description = "Diversity (entropy or count) of subcellular localization flags across a perturbation's target genes."
    rationale = "Perturbations targeting genes whose products localize to diverse subcellular compartments have broader downstream effects."
    inputs = ["knowledge"]
    params = {"metric": "entropy"}
    dim = 1

    def compute(self, ctx, perts, params):
        metric = params.get("metric", "entropy")

        ann = ctx.knowledge("protein_annotation")
        cache = ctx.cache

        if "loc_cols" not in cache:
            cols = []
            if ann is not None:
                colnames = ann.get("columns", [])
                for j, c in enumerate(colnames):
                    if c in ("secreted", "membrane", "endoplasmic_reticulum",
                             "golgi", "mitochondrion", "nucleus", "cytoplasm",
                             "lysosome", "peroxisome"):
                        cols.append(j)
            cache["loc_cols"] = cols

        loc_cols = cache["loc_cols"]
        n_loc = len(loc_cols)

        genes_map = ann.get("genes", {}) if ann is not None else {}

        cache_key = "loc_flags"
        if cache_key not in cache:
            flags = {}
            for g, vals in genes_map.items():
                if vals is None:
                    continue
                v = np.zeros(n_loc, dtype=float)
                for k, j in enumerate(loc_cols):
                    if j < len(vals) and vals[j] is not None:
                        try:
                            v[k] = 1.0 if float(vals[j]) != 0.0 else 0.0
                        except (TypeError, ValueError):
                            v[k] = 0.0
                flags[g] = v
            cache[cache_key] = flags
        flags = cache[cache_key]

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                val = 0.0
            else:
                counts = np.zeros(n_loc, dtype=float)
                seen = 0
                for g in targets:
                    f = flags.get(g)
                    if f is not None:
                        counts += f
                        seen += 1
                total = counts.sum()
                if total <= 0.0:
                    val = 0.0
                elif metric == "count":
                    val = float(np.count_nonzero(counts))
                else:
                    probs = counts / total
                    probs = probs[probs > 0]
                    val = float(-np.sum(probs * np.log(probs)))
            out[i, :, 0] = val

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
