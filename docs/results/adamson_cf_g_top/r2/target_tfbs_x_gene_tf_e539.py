import numpy as np
from genemila.features.api import Feature, register


@register
class TargetTfbsXGeneTf(Feature):
    name = "target_tfbs_x_gene_tf_e539"
    version = 1
    description = ("Product of the number of TF binding sites in the target promoter "
                   "and an indicator that gene g is a transcription factor.")
    rationale = ("Targets with dense TFBS may be regulatory hubs; their perturbation could "
                 "alter TF expression. Interaction of target TFBS count and gene TF indicator "
                 "may be predictive.")
    inputs = ["gene_annotation", "transcription_factors", "target_indices"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        tf_list = ctx.knowledge("transcription_factors")

        # Gene TF indicator
        tf_indicator = np.zeros(n_genes, dtype=float)
        if tf_list is not None:
            tf_set = set(tf_list)
            for j, g in enumerate(ctx.genes):
                if g in tf_set:
                    tf_indicator[j] = 1.0

        # Per-gene TFBS estimate from gene_annotation columns
        tfbs_per_gene = np.zeros(n_genes, dtype=float)
        if ann is not None:
            genes_ann = ann.get("genes", {})
            columns = ann.get("columns", [])
            col_idx = {c: i for i, c in enumerate(columns)}
            # Candidate columns that relate to promoter / TFBS density:
            cand = []
            for c in ("n_tss_within_100kb", "n_upstream_atg", "n_transcripts"):
                if c in col_idx:
                    cand.append(col_idx[c])
            for j, g in enumerate(ctx.genes):
                vals = genes_ann.get(g)
                if vals is None:
                    continue
                acc = 0.0
                for ci in cand:
                    if ci < len(vals) and vals[ci] is not None:
                        try:
                            v = float(vals[ci])
                            if np.isfinite(v):
                                acc += v
                        except (TypeError, ValueError):
                            pass
                tfbs_per_gene[j] = acc

        # Per-perturbation target TFBS count
        for i, p in enumerate(perts):
            tidx = ctx.target_indices(p)
            if tidx:
                tfbs_target = float(np.sum(tfbs_per_gene[tidx]))
            else:
                tfbs_target = 0.0
            out[i, :, 0] = tfbs_target * tf_indicator

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
