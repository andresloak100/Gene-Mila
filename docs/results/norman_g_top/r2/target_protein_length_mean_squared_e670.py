import numpy as np
from genemila.features.api import Feature, register


@register
class TargetProteinLengthMeanSquared(Feature):
    name = "target_protein_length_mean_squared_e670"
    version = 1
    description = "Square of the mean protein length (UniProt) of the perturbation's target genes."
    rationale = ("Larger proteins may carry more interaction domains, so a quadratic term "
                 "in mean target protein length may capture non-linear scaling of effects.")
    inputs = ["target_genes", "knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        # Load protein annotation knowledge once and memoise in ctx.cache.
        cache = ctx.cache
        if "protein_length_lookup_e670" not in cache:
            anno = ctx.knowledge("protein_annotation")
            lookup = {}
            if anno is not None:
                cols = anno.get("columns", [])
                genes = anno.get("genes", {})
                try:
                    idx = cols.index("protein_length")
                except ValueError:
                    idx = 0
                for sym, vals in genes.items():
                    if vals is None:
                        continue
                    try:
                        v = vals[idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        lookup[sym] = fv
            cache["protein_length_lookup_e670"] = lookup
        lookup = cache["protein_length_lookup_e670"]

        out = np.zeros((len(perts), ctx.n_genes, 1))
        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            lengths = [lookup[g] for g in targets if g in lookup]
            if lengths:
                mean_len = float(np.mean(lengths))
            else:
                mean_len = 0.0
            val = mean_len * mean_len
            if not np.isfinite(val):
                val = 0.0
            out[i, :, 0] = val
        return out
