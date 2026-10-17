import numpy as np
from genemila.features.api import Feature, register

@register
class TargetLocalizationDiversityE397(Feature):
    name = "target_localization_diversity_e397"
    version = 1
    description = "Shannon entropy of averaged subcellular localization flags across target genes."
    rationale = "Diversity of target protein localizations may modulate the additive response via multi-compartment effects."
    inputs = ["protein_annotation", "target_genes"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))

        ann = ctx.knowledge("protein_annotation")
        if ann is None:
            return out

        cols = ann.get("columns", [])
        genes = ann.get("genes", {})
        # localization flag columns
        loc_cols = ["secreted", "membrane", "endoplasmic_reticulum", "golgi",
                    "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome"]
        idxs = [cols.index(c) for c in loc_cols if c in cols]
        n_flags = len(idxs)
        if n_flags == 0:
            return out

        # cache per-gene localization vector
        cache = ctx.cache
        key = "_e397_locvec"
        if key not in cache:
            cache[key] = {}
        vec_cache = cache[key]

        def get_vec(g):
            if g in vec_cache:
                return vec_cache[g]
            v = None
            row = genes.get(g)
            if row is not None:
                v = np.zeros(n_flags, dtype=float)
                for j, ci in enumerate(idxs):
                    val = row[ci]
                    if val is not None:
                        try:
                            v[j] = 1.0 if float(val) > 0 else 0.0
                        except (TypeError, ValueError):
                            v[j] = 0.0
            vec_cache[g] = v
            return v

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            vecs = []
            for g in tg:
                v = get_vec(g)
                if v is not None:
                    vecs.append(v)
            if not vecs:
                continue
            avg = np.mean(np.array(vecs), axis=0)
            # Shannon entropy of the averaged flag vector (treat as distribution)
            s = avg.sum()
            if s <= 0:
                continue
            prob = avg / s
            prob = prob[prob > 0]
            ent = -np.sum(prob * np.log(prob))
            out[i, :, 0] = ent

        return out
