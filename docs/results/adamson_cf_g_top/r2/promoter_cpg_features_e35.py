import numpy as np
from genemila.features.api import Feature, register


@register
class PromoterCpgFeaturesE35(Feature):
    name = "promoter_cpg_features_e35"
    version = 1
    description = "Per-gene promoter features: gc_promoter, cpg_oe_promoter, n_tss_within_100kb from gene_annotation."
    rationale = ("Promoter CpG density and local TSS density may modulate CRISPRi efficiency and "
                 "transcriptional response; these are static per-gene covariates broadcast across perturbations.")
    inputs = ["knowledge:gene_annotation"]
    params = {"features": ["gc_promoter", "cpg_oe_promoter", "n_tss_within_100kb"]}
    dim = 3

    def compute(self, ctx, perts, params):
        feats = list(params.get("features",
                                ["gc_promoter", "cpg_oe_promoter", "n_tss_within_100kb"]))
        dim = len(feats)
        out = np.zeros((len(perts), ctx.n_genes, dim), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is None:
            return out

        columns = ann.get("columns", [])
        genes_tbl = ann.get("genes", {}) or {}
        col_idx = {c: i for i, c in enumerate(columns)}

        # Build (n_genes, dim) matrix aligned to ctx.genes
        mat = np.zeros((ctx.n_genes, dim), dtype=float)
        for j, fname in enumerate(feats):
            ci = col_idx.get(fname)
            if ci is None:
                continue
            for gi, g in enumerate(ctx.genes):
                vals = genes_tbl.get(g)
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
                if np.isfinite(fv):
                    mat[gi, j] = fv

        # Broadcast to all perturbations
        out[:] = mat[None, :, :]
        return out
