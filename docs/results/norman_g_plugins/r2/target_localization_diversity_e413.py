import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLocalizationDiversityE413(Feature):
    name = "target_localization_diversity_e413"
    version = 1
    description = "Shannon entropy of subcellular localization flag distribution across a perturbation's target genes."
    rationale = "Proteins in different compartments trigger distinct pathways; broader compartment diversity may broaden effects."
    inputs = ["knowledge"]
    params = {}
    dim = 1

    _LOC_KEYS = [
        "secreted", "membrane", "endoplasmic_reticulum", "golgi",
        "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome",
    ]

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))
        pa = ctx.knowledge("protein_annotation")
        if not pa:
            return out
        genes_tbl = pa.get("genes", {})
        cols = pa.get("columns", [])
        try:
            loc_idx = [cols.index(k) for k in self._LOC_KEYS]
        except ValueError:
            return out
        n_loc = len(loc_idx)

        # Precompute per-gene localization flag vector.
        cache = ctx.cache
        if "loc_flags" not in cache:
            flags = {}
            for g, vals in genes_tbl.items():
                if vals is None:
                    continue
                vec = np.zeros(n_loc, dtype=np.float64)
                ok = True
                for j, ci in enumerate(loc_idx):
                    v = vals[ci] if ci < len(vals) else None
                    if v is None:
                        ok = False
                        break
                    vec[j] = float(v)
                if ok:
                    flags[g] = vec
            cache["loc_flags"] = flags
        flags = cache["loc_flags"]

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            if not tg:
                continue
            counts = np.zeros(n_loc, dtype=np.float64)
            found = False
            for g in tg:
                v = flags.get(g)
                if v is not None:
                    counts += v
                    found = True
            if not found:
                continue
            tot = counts.sum()
            if tot <= 0:
                continue
            prob = counts / tot
            nz = prob[prob > 0]
            ent = -np.sum(nz * np.log(nz))
            out[i, :, 0] = ent
        return out
