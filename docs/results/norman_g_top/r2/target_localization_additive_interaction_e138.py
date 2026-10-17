import numpy as np
from genemila.features.api import Feature, register

@register
class TargetLocalizationAdditiveInteraction(Feature):
    name = "target_localization_additive_interaction_e138"
    version = 1
    description = ("For each subcellular localization flag from protein_annotation, the fraction "
                   "of p's target genes carrying that flag multiplied by the additive_response.")
    rationale = ("The subcellular localization of a target protein modulates how its perturbation "
                 "propagates: nuclear targets (TFs) tend to have broader transcriptional effects than "
                 "cytoplasmic or membrane ones. Interacting localization fractions with the additive "
                 "response lets the model rescale the generic response per compartment.")
    inputs = ["protein_annotation", "additive_response"]
    params = {"flags": ["nucleus", "cytoplasm", "membrane", "secreted",
                        "endoplasmic_reticulum", "golgi", "mitochondrion",
                        "lysosome", "peroxisome"]}
    dim = 9

    def compute(self, ctx, perts, params):
        flags = list(params.get("flags", self.params["flags"]))
        n_flags = len(flags)
        n_perts = len(perts)
        n_genes = ctx.n_genes

        # Fetch additive_response (n_perts, n_genes, 1)
        add = ctx.feature("additive_response", perts)
        add = np.asarray(add, dtype=float)
        if add.ndim == 3:
            add = add[:, :, 0]
        elif add.ndim == 1:
            add = add.reshape(n_perts, n_genes)
        add = np.nan_to_num(add, nan=0.0, posinf=0.0, neginf=0.0)

        # Load protein_annotation
        pa = ctx.knowledge("protein_annotation")
        columns = []
        genes_map = {}
        if isinstance(pa, dict):
            columns = list(pa.get("columns", []))
            genes_map = pa.get("genes", {}) or {}

        # Build flag -> column index
        col_idx = {c: i for i, c in enumerate(columns)}

        # Precompute per-gene flag indicator matrix (n_genes, n_flags)
        flag_mat = np.zeros((n_genes, n_flags), dtype=float)
        for fi, flag in enumerate(flags):
            ci = col_idx.get(flag, None)
            if ci is None:
                continue
            for gi, g in enumerate(ctx.genes):
                vals = genes_map.get(g, None)
                if vals is None:
                    continue
                try:
                    v = vals[ci]
                except (IndexError, TypeError):
                    continue
                if v is None:
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv) and fv != 0.0:
                    flag_mat[gi, fi] = 1.0

        out = np.zeros((n_perts, n_genes, n_flags), dtype=float)

        for i, p in enumerate(perts):
            tgt = ctx.target_indices(p)
            if len(tgt) == 0:
                continue
            tgt = np.asarray(tgt, dtype=int)
            # mean flag across targets -> (n_flags,)
            frac = flag_mat[tgt, :].mean(axis=0)
            # broadcast: (n_genes,) * (n_flags,) -> (n_genes, n_flags)
            out[i, :, :] = add[i, :, None] * frac[None, :]

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
