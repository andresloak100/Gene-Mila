import numpy as np
from genemila.features.api import Feature, register


@register
class TargetProteinLocalizationE53(Feature):
    name = "target_protein_localization_e53"
    version = 1
    description = "Binary localization flags of the perturbation's target protein, broadcast to all genes."
    rationale = (
        "Perturbing membrane or secreted proteins may have different downstream effects "
        "than perturbing nuclear or cytoplasmic proteins due to compartmentalization."
    )
    inputs = ["protein_annotation", "target_genes"]
    params = {"localization_flags": ["membrane", "secreted", "nucleus", "cytoplasm"]}
    dim = 4

    def compute(self, ctx, perts, params):
        flags = list(params.get("localization_flags", self.params["localization_flags"]))
        dim = len(flags)
        out = np.zeros((len(perts), ctx.n_genes, dim), dtype=float)

        pa = ctx.knowledge("protein_annotation")
        if pa is None:
            return out

        columns = pa.get("columns", [])
        genes_tbl = pa.get("genes", {})
        col_index = {c: i for i, c in enumerate(columns)}

        # Precompute per-gene flag vectors
        flag_vec = {}
        for g, vals in genes_tbl.items():
            if vals is None:
                continue
            v = np.zeros(dim, dtype=float)
            for j, f in enumerate(flags):
                idx = col_index.get(f)
                if idx is None or idx >= len(vals):
                    continue
                val = vals[idx]
                if val is None:
                    continue
                try:
                    v[j] = 1.0 if float(val) > 0 else 0.0
                except (TypeError, ValueError):
                    continue
            flag_vec[g] = v

        zero = np.zeros(dim, dtype=float)
        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            if not tg:
                continue
            vec = zero
            for t in tg:
                if t in flag_vec:
                    vec = flag_vec[t]
                    break
            out[i, :, :] = vec

        return out
