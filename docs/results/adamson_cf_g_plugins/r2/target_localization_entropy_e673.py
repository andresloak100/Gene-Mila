import numpy as np
from genemila.features.api import Feature, register

@register
class TargetLocalizationEntropyE673(Feature):
    name = "target_localization_entropy_e673"
    version = 1
    description = ("Shannon entropy of the target protein's compartment localization flags "
                   "(from protein_annotation), broadcast to all genes.")
    rationale = ("Targets localized to multiple compartments have more diverse interactions "
                 "and produce larger expression changes; entropy captures the distribution "
                 "of localization more informatively than binary indicators.")
    inputs = ["control_cells", "protein_annotation"]
    params = {}
    dim = 1

    COMPARTMENTS = ["secreted", "membrane", "endoplasmic_reticulum", "golgi",
                    "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome"]

    def _entropy(self, flags):
        flags = np.asarray(flags, dtype=float)
        total = flags.sum()
        if total <= 0:
            return 0.0
        p = flags / total
        p = p[p > 0]
        return float(-(p * np.log(p)).sum())

    def compute(self, ctx, perts, params):
        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("protein_annotation")
        cols = None
        genes = {}
        if ann is not None:
            cols = ann.get("columns", [])
            genes = ann.get("genes", {}) or {}

        # Precompute per-gene entropy lookup
        ent_cache = {}
        if cols is not None:
            idxs = []
            for c in self.COMPARTMENTS:
                if c in cols:
                    idxs.append(cols.index(c))
                else:
                    idxs.append(None)
            for g, vals in genes.items():
                if vals is None:
                    continue
                fl = []
                for j in idxs:
                    if j is None or j >= len(vals) or vals[j] is None:
                        fl.append(0.0)
                    else:
                        try:
                            fl.append(float(vals[j]))
                        except (TypeError, ValueError):
                            fl.append(0.0)
                ent_cache[g] = self._entropy(fl)

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            if not tg:
                continue
            e = ent_cache.get(tg[0], 0.0)
            if e != 0.0:
                out[i, :, 0] = e
        return out
