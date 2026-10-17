import numpy as np
from genemila.features.api import Feature, register


@register
class AnnotationProjectionTargetInteraction(Feature):
    name = "annotation_projection_target_interaction_e173"
    version = 1
    description = (
        "Dot product between a random projection of the target gene's annotation "
        "vector and the random projection of gene g's annotation vector, summed "
        "over multiple random projection components."
    )
    rationale = (
        "Gene annotation encodes structural/functional properties. A random "
        "projection of these features, interacted between target and gene, can "
        "capture context-specific nonlinear gene-target relationships that "
        "additive features miss."
    )
    inputs = ["gene_annotation", "target_indices"]
    params = {"n_components": 10, "seed": 0}
    dim = 1

    def compute(self, ctx, perts, params):
        n_components = int(params.get("n_components", 10))
        seed = int(params.get("seed", 0))
        n_genes = ctx.n_genes

        # Load gene annotation prior knowledge.
        ann = ctx.knowledge("gene_annotation")
        ann_matrix = self._build_annotation_matrix(ctx, ann)  # (n_genes, n_feat)

        n_feat = ann_matrix.shape[1]
        if n_feat == 0:
            return np.zeros((len(perts), n_genes, 1))

        # Random projection matrix (n_feat, n_components), fixed via seed.
        rng = np.random.RandomState(seed)
        proj = rng.normal(size=(n_feat, n_components)) / np.sqrt(max(n_feat, 1))

        # Projected annotation for every gene: (n_genes, n_components)
        gene_proj = ann_matrix.dot(proj)

        out = np.zeros((len(perts), n_genes, 1))
        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if len(tgt_idx) == 0:
                continue
            # Average projection over target genes (usually one).
            tgt_proj = gene_proj[tgt_idx, :].mean(axis=0)  # (n_components,)
            # Dot product with each gene's projection -> (n_genes,)
            out[i, :, 0] = gene_proj.dot(tgt_proj)
        return out

    @staticmethod
    def _build_annotation_matrix(ctx, ann):
        """Build (n_genes, n_numeric_features) annotation matrix aligned to ctx.genes."""
        n_genes = ctx.n_genes
        if not ann or "genes" not in ann:
            return np.zeros((n_genes, 0), dtype=float)

        columns = ann.get("columns", [])
        genes = ann.get("genes", {})
        n_feat = len(columns)
        mat = np.zeros((n_genes, n_feat), dtype=float)

        # Only use numeric columns (skip amino-acid fractions that may be null,
        # but we include them when numeric).
        for gi, g in enumerate(ctx.genes):
            vals = genes.get(g)
            if vals is None:
                continue
            for ci in range(min(n_feat, len(vals))):
                v = vals[ci]
                if v is None:
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv):
                    mat[gi, ci] = fv

        # Standardize columns (robust: skip constant columns).
        std = mat.std(axis=0)
        mean = mat.mean(axis=0)
        valid = std > 1e-8
        if np.any(valid):
            mat[:, valid] = (mat[:, valid] - mean[valid]) / std[valid]
        # Zero out non-valid columns.
        mat[:, ~valid] = 0.0
        return mat
