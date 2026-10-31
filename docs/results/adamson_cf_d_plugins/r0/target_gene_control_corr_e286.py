import numpy as np
from genemila.features.api import Feature, FeatureContext, register

@register
class TargetGeneControlCorrE286(Feature):
    name = "target_gene_control_corr_e286"
    version = 1
    description = "Pearson correlation between gene g and the target gene of p across control cells."
    rationale = "Co-expressed genes are likely co-regulated; perturbing one alters the other's expression."
    inputs = ["control_cells", "gene_corr"]
    params = {}
    dim = 1

    def compute(self, ctx: FeatureContext, perts: list[str], params: dict) -> np.ndarray:
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        corr = ctx.gene_corr
        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            valid = [t for t in tgt_idx if 0 <= t < n_genes]
            if not valid:
                continue
            rows = corr[valid, :]
            vals = np.nanmean(rows, axis=0)
            vals = np.where(np.isfinite(vals), vals, 0.0)
            out[i, :, 0] = vals
        return out
