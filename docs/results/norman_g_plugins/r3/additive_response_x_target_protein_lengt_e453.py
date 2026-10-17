import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveResponseXTargetProteinLength(Feature):
    name = "additive_response_x_target_protein_lengt_e453"
    version = 1
    description = ("Product of the additive_response feature and the mean protein length "
                   "of the perturbation's target genes.")
    rationale = ("Longer proteins may have more domains or interactions, so target protein "
                 "length could modulate the magnitude of the additive perturbation response.")
    inputs = ["protein_annotation", "feature:additive_response"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        n_perts = len(perts)

        # additive_response feature (n_perts, n_genes, 1)
        try:
            add = ctx.feature("additive_response", perts, params=None)
        except Exception:
            add = None

        if add is None:
            # Fallback: no additive_response available -> zeros
            return np.zeros((n_perts, n_genes, 1), dtype=float)

        add = np.asarray(add, dtype=float)
        if add.ndim == 2:
            add = add[:, :, None]

        # Load protein_annotation
        pa = ctx.knowledge("protein_annotation")
        prot_len = {}
        if pa is not None:
            genes_tbl = pa.get("genes", {})
            cols = pa.get("columns", [])
            try:
                pl_idx = cols.index("protein_length")
            except ValueError:
                pl_idx = 0
            for g, vals in genes_tbl.items():
                if vals is None:
                    continue
                try:
                    v = vals[pl_idx]
                except Exception:
                    continue
                if v is None:
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv):
                    prot_len[g] = fv

        out = np.zeros((n_perts, n_genes, 1), dtype=float)

        # Cache per-perturbation mean protein length
        cache = ctx.cache
        key = "e453_mean_prot_len"
        mean_map = cache.get(key)
        if mean_map is None:
            mean_map = {}
            for p in perts:
                tg = ctx.target_genes(p)
                vals = [prot_len[g] for g in tg if g in prot_len]
                if vals:
                    mean_map[p] = float(np.mean(vals))
                else:
                    mean_map[p] = 0.0
            cache[key] = mean_map

        for i, p in enumerate(perts):
            m = mean_map.get(p, 0.0)
            out[i, :, 0] = add[i, :, 0] * m

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
