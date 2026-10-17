import numpy as np
from genemila.features.api import Feature, register

@register
class TargetProteinLengthNormalized(Feature):
    name = "target_protein_length_normalized_e446"
    version = 1
    description = "Target gene's protein length divided by median protein length across all genes."
    rationale = ("Longer proteins may participate in more interactions or regulatory roles, "
                 "so normalized protein length of the target may shape the perturbation response.")
    inputs = ["protein_annotation", "target_genes"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        pa = ctx.knowledge("protein_annotation")
        if not pa or "genes" not in pa or "columns" not in pa:
            return out

        cols = list(pa["columns"])
        try:
            pl_idx = cols.index("protein_length")
        except ValueError:
            return out

        genes_table = pa["genes"]
        lengths = []
        for sym, vals in genes_table.items():
            if vals is None:
                continue
            try:
                v = vals[pl_idx]
            except (IndexError, TypeError):
                continue
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv) and fv > 0:
                lengths.append(fv)

        if not lengths:
            return out
        median_len = float(np.median(np.asarray(lengths, dtype=float)))
        if not np.isfinite(median_len) or median_len <= 0:
            return out

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            if not tgenes:
                continue
            # use first target with available protein length
            ratio = 0.0
            found = False
            for tg in tgenes:
                vals = genes_table.get(tg)
                if vals is None:
                    continue
                try:
                    v = vals[pl_idx]
                except (IndexError, TypeError):
                    continue
                if v is None:
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv):
                    ratio = fv / median_len
                    found = True
                    break
            if not found:
                continue
            # broadcast target ratio to all genes
            out[i, :, 0] = ratio

        out[~np.isfinite(out)] = 0.0
        return out
