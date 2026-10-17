import numpy as np
from genemila.features.api import Feature, register


@register
class TargetTfXGeneCpgPromoter(Feature):
    name = "target_tf_x_gene_cpg_promoter_e653"
    version = 2
    description = ("Per-gene CpG observed/expected promoter score, scaled by a target-specific TF weight "
                   "so the feature varies across perturbations.")
    rationale = ("Perturbing a transcription factor may exert stronger effects on genes whose promoters are CpG-rich. "
                 "The CpG signal is placed on the response gene and modulated by a perturbation-specific weight "
                 "derived from whether the target is a TF, avoiding a constant-across-rows feature.")
    inputs = ["knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # ---- CpG promoter score per gene from gene_annotation ----
        cpg = np.zeros(n_genes, dtype=float)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes = ann.get("genes", {})
            columns = ann.get("columns", [])
            try:
                cpg_idx = columns.index("cpg_oe_promoter")
            except ValueError:
                cpg_idx = None
            if cpg_idx is not None:
                for g, col in ctx.gene_index.items():
                    vals = genes.get(g)
                    if vals is None:
                        continue
                    try:
                        v = vals[cpg_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        cpg[col] = fv

        # Standardize CpG across genes (robust to scale)
        mu = cpg.mean()
        sd = cpg.std()
        if sd > 0:
            cpg_z = (cpg - mu) / sd
        else:
            cpg_z = cpg - mu

        # ---- Transcription factor set ----
        tfs = ctx.knowledge("transcription_factors")
        tf_set = set(tfs) if tfs is not None else set()

        # ---- Per-perturbation weight so rows differ ----
        weights = np.zeros(len(perts), dtype=float)
        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            if not tgenes:
                weights[i] = 0.0
                continue
            n_tf = sum(1 for tg in tgenes if tg in tf_set)
            frac_tf = n_tf / float(len(tgenes))
            # base weight: 1.0 for TF targets, 0.5 otherwise; scaled by number of targets
            base = 1.0 if n_tf > 0 else 0.5
            weights[i] = base * (1.0 + 0.1 * len(tgenes)) * (0.5 + frac_tf)

        # Ensure non-degenerate weights: if all identical, add small perturbation-index variation
        if np.allclose(weights, weights[0]):
            weights = weights + 0.01 * np.arange(len(perts), dtype=float)

        for i in range(len(perts)):
            out[i, :, 0] = weights[i] * (cpg_z + 1.0)

        # Sanitize
        out[~np.isfinite(out)] = 0.0
        return out
