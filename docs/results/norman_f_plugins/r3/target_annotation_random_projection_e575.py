import numpy as np
from genemila.features.api import Feature, register


@register
class TargetAnnotationRandomProjection(Feature):
    name = "target_annotation_random_projection_e575"
    version = 1
    description = "Average annotation vectors of target genes projected to 5 dims via a fixed random Gaussian matrix."
    rationale = "A low-dimensional random projection of target gene annotation captures unmodeled target properties without overfitting."
    inputs = ["knowledge"]
    params = {"n_components": 5, "seed": 575}
    dim = 5

    def compute(self, ctx, perts, params):
        n_components = int(params.get("n_components", 5))
        seed = int(params.get("seed", 575))
        n_genes = ctx.n_genes

        ann = ctx.knowledge("gene_annotation")
        if ann is None:
            return np.zeros((len(perts), n_genes, n_components))

        genes_block = ann.get("genes", {}) if isinstance(ann, dict) else {}
        columns = ann.get("columns", []) if isinstance(ann, dict) else []

        # Determine feature dimension from data
        feat_dim = None
        for g, vals in genes_block.items():
            if vals is not None:
                feat_dim = len(vals)
                break
        if feat_dim is None:
            feat_dim = len(columns) if columns else 0
        if feat_dim == 0:
            return np.zeros((len(perts), n_genes, n_components))

        # Build annotation matrix aligned to ctx.genes
        ann_mat = np.zeros((n_genes, feat_dim), dtype=np.float64)
        for gi, g in enumerate(ctx.genes):
            vals = genes_block.get(g)
            if vals is None:
                continue
            v = np.asarray(vals, dtype=np.float64)
            m = min(feat_dim, v.shape[0])
            # replace non-finite with 0
            vv = v[:m]
            vv = np.where(np.isfinite(vv), vv, 0.0)
            ann_mat[gi, :m] = vv

        # Fixed random projection matrix (feat_dim x n_components)
        rng = np.random.RandomState(seed)
        proj = rng.randn(feat_dim, n_components) / np.sqrt(max(feat_dim, 1))

        # Precompute projection of every gene's annotation vector
        gene_proj = ann_mat @ proj  # (n_genes, n_components)

        out = np.zeros((len(perts), n_genes, n_components), dtype=np.float64)
        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            if not tgenes:
                continue
            idxs = [ctx.gene_index[g] for g in tgenes if g in ctx.gene_index]
            if not idxs:
                continue
            avg = gene_proj[idxs].mean(axis=0)  # (n_components,)
            out[i, :, :] = avg[None, :]

        out = np.where(np.isfinite(out), out, 0.0)
        return out
