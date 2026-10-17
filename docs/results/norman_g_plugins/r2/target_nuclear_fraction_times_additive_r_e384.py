import numpy as np
from genemila.features.api import Feature, register


@register
class TargetNuclearFractionTimesAdditiveR(Feature):
    name = "target_nuclear_fraction_times_additive_r_e384"
    version = 1
    description = ("Fraction of p's target genes whose UniProt annotation includes 'nucleus', "
                   "multiplied by the additive_response feature.")
    rationale = ("Nuclear-localized target proteins may more directly influence transcription, "
                 "modulating the additive response strength.")
    inputs = ["protein_annotation", "feature"]
    params = {}
    dim = 1

    def _nuclear_flags(self, ctx):
        cache = ctx.cache
        key = "_e384_nuclear_flags"
        if key in cache:
            return cache[key]
        flags = np.zeros(ctx.n_genes, dtype=float)
        ann = ctx.knowledge("protein_annotation")
        if ann is not None:
            genes = ann.get("genes", {})
            cols = ann.get("columns", [])
            if "nucleus" in cols:
                nuc_idx = cols.index("nucleus")
                for g, vals in genes.items():
                    if g in ctx.gene_index and vals is not None:
                        try:
                            v = vals[nuc_idx]
                        except (IndexError, TypeError):
                            continue
                        if v is None:
                            continue
                        try:
                            flags[ctx.gene_index[g]] = 1.0 if float(v) > 0 else 0.0
                        except (TypeError, ValueError):
                            continue
        cache[key] = flags
        return flags

    def compute(self, ctx, perts, params):
        nuc = self._nuclear_flags(ctx)
        add = ctx.feature("additive_response", perts)
        add = np.asarray(add, dtype=float)
        if add.ndim == 1:
            add = add.reshape(len(perts), ctx.n_genes, 1)
        base = add[:, :, 0]

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            tidx = ctx.target_indices(p)
            if len(tidx) == 0:
                frac = 0.0
            else:
                frac = float(np.mean(nuc[tidx]))
            out[i, :, 0] = frac * base[i]
        return out
