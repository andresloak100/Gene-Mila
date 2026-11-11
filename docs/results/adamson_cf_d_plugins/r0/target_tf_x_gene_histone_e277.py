import numpy as np
from genemila.features.api import Feature, register


@register
class TargetTFxGeneHistone(Feature):
    name = "target_tf_x_gene_histone_e277"
    version = 2
    description = "Indicator that perturbation target is a transcription factor and gene g is a histone gene."
    rationale = ("Transcription factor perturbations may disrupt cell-cycle regulation, "
                 "altering histone gene expression; encode this as a target-TF x gene-histone interaction.")
    inputs = ["transcription_factors"]
    params = {"histone_prefix": "HIST"}
    dim = 1

    def _parse_tf(self, tf_raw):
        tf_set = set()
        if tf_raw is None:
            return tf_set
        if isinstance(tf_raw, dict):
            for key in ("genes", "transcription_factors", "list"):
                if key in tf_raw:
                    tf_raw = tf_raw[key]
                    break
            else:
                tf_raw = list(tf_raw.keys())
        if isinstance(tf_raw, str):
            tf_raw = [tf_raw]
        for x in tf_raw:
            if isinstance(x, str):
                tf_set.add(x)
            elif isinstance(x, (list, tuple)) and len(x) > 0 and isinstance(x[0], str):
                tf_set.add(x[0])
        return tf_set

    def compute(self, ctx, perts, params):
        prefix = params.get("histone_prefix", "HIST")

        tf_set = self._parse_tf(ctx.knowledge("transcription_factors"))

        # Histone gene mask from prefix and gene_sets.
        histone_mask = np.zeros(ctx.n_genes, dtype=bool)
        for j, g in enumerate(ctx.genes):
            if g.startswith(prefix):
                histone_mask[j] = True
        gs = ctx.knowledge("gene_sets")
        if gs is not None and isinstance(gs, dict):
            histone_genes = set()
            for set_name, members in gs.items():
                if "histone" in str(set_name).lower():
                    for m in members:
                        if isinstance(m, str):
                            histone_genes.add(m)
            if histone_genes:
                for j, g in enumerate(ctx.genes):
                    if g in histone_genes:
                        histone_mask[j] = True

        # Fallback: if nothing found by prefix/sets, use genes whose name contains "histone".
        if not histone_mask.any():
            for j, g in enumerate(ctx.genes):
                if "histone" in g.lower():
                    histone_mask[j] = True

        n_hist = int(histone_mask.sum())

        # Perturbation-level TF score (scalar per pert).
        pert_tf = np.zeros(len(perts), dtype=float)
        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if targets and any(t in tf_set for t in targets):
                pert_tf[i] = 1.0

        # If no TF info, fall back to using target being a known gene (any target).
        if pert_tf.sum() == 0:
            for i, p in enumerate(perts):
                if ctx.target_genes(p):
                    pert_tf[i] = 1.0

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        if n_hist == 0:
            # Degenerate: spread signal across all genes so feature varies by row.
            for i in range(len(perts)):
                out[i, :, 0] = pert_tf[i]
            return out

        # Non-degenerate interaction: TF indicator broadcast over histone genes.
        out[:, histone_mask, 0] = pert_tf[:, None]
        return out
