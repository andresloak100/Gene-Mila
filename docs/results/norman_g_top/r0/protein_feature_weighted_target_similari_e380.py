import numpy as np
from genemila.features.api import Feature, register


@register
class ProteinFeatureWeightedTargetSimilarityE380(Feature):
    name = "protein_feature_weighted_target_similari_e380"
    version = 1
    description = ("Target-response similarity of each gene g to perturbation p, "
                   "weighted by a protein annotation feature of g.")
    rationale = ("Multiplying target-response similarity by a protein structural "
                 "feature (e.g. transmembrane count) captures nonlinear interactions "
                 "between membrane/secreted proteins and CRISPRa response.")
    inputs = ["control_cells", "gene_corr", "train_delta", "protein_annotation"]
    params = {"protein_feature": "n_transmembrane", "k": 10}
    dim = 1

    def _protein_values(self, ctx, feature_name):
        pa = ctx.knowledge("protein_annotation")
        vals = np.zeros(ctx.n_genes, dtype=float)
        if pa is None:
            return vals
        cols = pa.get("columns", [])
        if feature_name not in cols:
            return vals
        ci = cols.index(feature_name)
        genes = pa.get("genes", {})
        for i, g in enumerate(ctx.genes):
            row = genes.get(g)
            if row is None:
                continue
            v = row[ci]
            if v is None:
                continue
            try:
                v = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(v):
                vals[i] = v
        return vals

    def compute(self, ctx, perts, params):
        feature_name = params.get("protein_feature", "n_transmembrane")
        k = int(params.get("k", 10))

        prot = self._protein_values(ctx, feature_name)

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        corr = ctx.gene_corr
        n_genes = ctx.n_genes

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue

            # similarity of each gene g to the perturbation's target set:
            # mean correlation of g with target genes (symmetric, order-independent)
            sim = corr[:, tgt_idx].mean(axis=1)  # (n_genes,)
            sim = np.nan_to_num(sim, nan=0.0, posinf=0.0, neginf=0.0)

            out[i, :, 0] = sim * prot

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
