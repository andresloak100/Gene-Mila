import numpy as np
from genemila.features.api import Feature, register


@register
class TargetPairNonadditivityProteinLengthE498(Feature):
    name = "target_pair_nonadditivity_protein_length_e498"
    version = 1
    description = ("For pair perturbations, ratio (larger/smaller) of mean protein lengths "
                   "of the two targets, multiplied by target_pair_nonadditivity_e263; 0 for singles.")
    rationale = ("Protein length may modulate interaction strength; scaling the non-additive "
                 "residual by the target size ratio could improve pair predictions.")
    inputs = ["knowledge", "feature"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        # Fetch the underlying non-additivity feature once for all perturbations.
        try:
            nonadd = ctx.feature("target_pair_nonadditivity_e263", perts)
            nonadd = np.asarray(nonadd, dtype=float)
            if nonadd.ndim == 2:
                nonadd = nonadd[:, :, None]
        except Exception:
            nonadd = None

        # Load protein lengths from prior knowledge.
        prot = None
        try:
            prot = ctx.knowledge("protein_annotation")
        except Exception:
            prot = None

        plen_map = {}
        if isinstance(prot, dict):
            genes_tab = prot.get("genes", {})
            cols = prot.get("columns", [])
            if isinstance(cols, list) and "protein_length" in cols and isinstance(genes_tab, dict):
                idx = cols.index("protein_length")
                for g, vals in genes_tab.items():
                    try:
                        v = vals[idx]
                        if v is not None:
                            fv = float(v)
                            if np.isfinite(fv) and fv > 0:
                                plen_map[g] = fv
                    except Exception:
                        continue

        for i, p in enumerate(perts):
            if nonadd is None:
                continue
            tg = ctx.target_genes(p)
            if tg is None or len(tg) != 2:
                continue
            lengths = [plen_map.get(g) for g in tg]
            if lengths[0] is None or lengths[1] is None:
                continue
            a, b = lengths
            lo, hi = (a, b) if a <= b else (b, a)
            if lo <= 0:
                continue
            ratio = hi / lo
            out[i, :, 0] = ratio * nonadd[i, :, 0]

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
