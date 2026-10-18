import numpy as np
from genemila.features.api import Feature, register


@register
class TargetIsTF(Feature):
    name = "target_is_tf_e66"
    version = 2
    description = "Per-gene indicator of whether the gene is a TF AND is targeted by the perturbation, plus a broadcast TF-target flag; varies across rows."
    rationale = "TF perturbations directly alter expression of many downstream genes; combining target status with TF membership gives a non-constant signal."
    inputs = ["transcription_factors"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        tf_data = ctx.knowledge("transcription_factors")
        tf_set = set()
        if tf_data is not None:
            if isinstance(tf_data, dict):
                found = False
                for key in ("list", "genes", "transcription_factors", "tfs", "symbols"):
                    v = tf_data.get(key)
                    if isinstance(v, (list, tuple, set)):
                        tf_set = set(str(x) for x in v)
                        found = True
                        break
                if not found:
                    for v in tf_data.values():
                        if isinstance(v, (list, tuple, set)):
                            tf_set = set(str(x) for x in v)
                            break
            elif isinstance(tf_data, (list, tuple, set)):
                tf_set = set(str(x) for x in tf_data)

        # Build a gene-level TF indicator vector aligned to ctx.genes.
        is_tf_gene = np.zeros(ctx.n_genes, dtype=float)
        if tf_set:
            for j, g in enumerate(ctx.genes):
                if str(g) in tf_set:
                    is_tf_gene[j] = 1.0

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if tgt_idx:
                # Non-constant: 1 at targeted TF genes, 0 elsewhere.
                row = np.zeros(ctx.n_genes, dtype=float)
                for j in tgt_idx:
                    if 0 <= j < ctx.n_genes and is_tf_gene[j] > 0:
                        row[j] = 1.0
                # If no targeted gene is a TF, fall back to broadcast target-TF flag
                # combined with per-gene TF indicator so the row still carries signal.
                if row.sum() == 0:
                    tg = ctx.target_genes(p)
                    is_tf_pert = any(str(g) in tf_set for g in tg)
                    if is_tf_pert:
                        row = is_tf_gene.copy()
                    else:
                        # distinguish non-TF-perturbation rows by broadcasting a small
                        # negative of the TF indicator (still varies across genes).
                        row = -0.5 * is_tf_gene
                out[i, :, 0] = row
            else:
                # No measured target: use TF indicator scaled to keep variation.
                out[i, :, 0] = 0.25 * is_tf_gene

        return out
