import numpy as np
from genemila.features.api import Feature, register


def _jaccard(a, b):
    union = np.logical_or(a, b).sum(axis=-1)
    inter = np.logical_and(a, b).sum(axis=-1)
    with np.errstate(divide="ignore", invalid="ignore"):
        j = np.where(union > 0, inter / union, 0.0)
    return j


@register
class TargetCompartmentSimilarityTimesAdditive(Feature):
    name = "target_compartment_similarity_times_addi_e322"
    version = 1
    description = ("Mean Jaccard similarity between subcellular localization profiles of p's "
                   "target genes (or between target and gene g for singles) times additive_response.")
    rationale = ("Proteins in the same subcellular compartment may share pathways, producing "
                 "synergistic effects; similarity modulates the additive baseline.")
    inputs = ["protein_annotation", "target_genes", "additive_response"]
    params = {}
    dim = 1

    _COMPARTMENTS = ["secreted", "membrane", "endoplasmic_reticulum", "golgi",
                     "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome"]

    def _profiles(self, ctx):
        cache = ctx.cache
        key = "_compartment_profiles_e322"
        if key in cache:
            return cache[key]
        ann = ctx.knowledge("protein_annotation")
        n_genes = ctx.n_genes
        prof = np.zeros((n_genes, len(self._COMPARTMENTS)), dtype=bool)
        if ann is not None:
            genes_map = ann.get("genes", {})
            columns = ann.get("columns", [])
            col_idx = {c: i for i, c in enumerate(columns)}
            flag_cols = [col_idx[c] for c in self._COMPARTMENTS if c in col_idx]
            for g, gi in ctx.gene_index.items():
                vals = genes_map.get(g)
                if vals is None:
                    continue
                for k, c in enumerate(self._COMPARTMENTS):
                    ci = col_idx.get(c)
                    if ci is None:
                        continue
                    v = vals[ci]
                    if v is not None:
                        try:
                            prof[gi, k] = float(v) > 0.5
                        except (TypeError, ValueError):
                            pass
        cache[key] = prof
        return prof

    def compute(self, ctx, perts, params):
        prof = self._profiles(ctx)  # (n_genes, n_comp)
        add = ctx.feature("additive_response", perts)  # (n, n_genes, 1)
        add = add[:, :, 0]

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            tgt_prof = prof[tgt_idx]  # (t, n_comp)

            if len(tgt_idx) == 1:
                # Jaccard between target and every gene g
                tvec = tgt_prof[0]  # (n_comp,)
                inter = np.logical_and(prof, tvec).sum(axis=1)
                union = np.logical_or(prof, tvec).sum(axis=1)
                with np.errstate(divide="ignore", invalid="ignore"):
                    sim = np.where(union > 0, inter / union, 0.0)
            else:
                # Mean pairwise Jaccard among targets, same value for all g
                t = len(tgt_idx)
                vals = []
                for a in range(t):
                    for b in range(a + 1, t):
                        va = tgt_prof[a]
                        vb = tgt_prof[b]
                        u = np.logical_or(va, vb).sum()
                        it = np.logical_and(va, vb).sum()
                        vals.append(it / u if u > 0 else 0.0)
                mean_sim = float(np.mean(vals)) if vals else 0.0
                sim = np.full(ctx.n_genes, mean_sim, dtype=float)

            out[i, :, 0] = sim * add[i]

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
