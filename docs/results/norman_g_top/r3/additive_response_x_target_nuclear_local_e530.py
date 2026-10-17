import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveResponseXTargetNuclearLocalE530(Feature):
    name = "additive_response_x_target_nuclear_local_e530"
    version = 1
    description = ("Product of additive_response and a binary indicator that is 1 if any "
                   "target gene's protein is annotated as nucleus-localized, else 0.")
    rationale = ("CRISPRa acts on transcription; perturbations whose target proteins are "
                 "nuclear may have more direct downstream effects, modulating the additive response.")
    inputs = ["protein_annotation", "train_delta"]
    params = {}
    dim = 1

    def _nuclear_flags(self, ctx):
        cache = ctx.cache
        key = "e530_nuclear_flags"
        if key in cache:
            return cache[key]
        ann = ctx.knowledge("protein_annotation")
        flags = np.zeros(ctx.n_genes, dtype=float)
        if ann is not None:
            cols = ann.get("columns", [])
            genes = ann.get("genes", {}) or {}
            try:
                nuc_idx = cols.index("nucleus")
            except ValueError:
                nuc_idx = None
            if nuc_idx is not None:
                for g, col in ctx.gene_index.items():
                    vals = genes.get(g)
                    if vals is None:
                        continue
                    try:
                        v = vals[nuc_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is not None and float(v) == 1.0:
                        flags[col] = 1.0
        cache[key] = flags
        return flags

    def compute(self, ctx, perts, params):
        nuc = self._nuclear_flags(ctx)
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            tgt = ctx.target_indices(p)
            if not tgt:
                continue
            mult = 1.0 if np.any(nuc[tgt] > 0.0) else 0.0
            if mult == 0.0:
                continue
            _, d = ctx.train_delta(exclude=p)
            add = d.mean(axis=0)
            out[i, :, 0] = add * mult
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
