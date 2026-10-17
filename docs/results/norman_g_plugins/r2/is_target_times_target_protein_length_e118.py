import numpy as np
from genemila.features.api import Feature, register


@register
class IsTargetTimesTargetProteinLengthE118(Feature):
    name = "is_target_times_target_protein_length_e118"
    version = 1
    description = "Product of is_target and the mean protein length of the perturbation's target genes."
    rationale = ("Protein length correlates with functional complexity; CRISPRa of longer proteins "
                 "may produce larger changes in the target gene itself, so the direct-target effect "
                 "may scale with target protein length.")
    inputs = ["protein_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        # Load protein annotation once and cache protein length per gene.
        cache = ctx.cache
        key = "_e118_protein_length"
        if key not in cache:
            plen = {}
            ann = ctx.knowledge("protein_annotation")
            if ann is not None:
                genes = ann.get("genes", {})
                columns = ann.get("columns", [])
                try:
                    idx = columns.index("protein_length")
                except ValueError:
                    idx = 0
                for g, vals in genes.items():
                    if vals is None:
                        continue
                    try:
                        v = vals[idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        v = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(v):
                        plen[g] = v
            cache[key] = plen
        plen = cache[key]

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue
            lengths = [plen[g] for g in targets if g in plen]
            if not lengths:
                continue
            mean_len = float(np.mean(lengths))
            for gi in ctx.target_indices(p):
                out[i, gi, 0] = mean_len

        return out
