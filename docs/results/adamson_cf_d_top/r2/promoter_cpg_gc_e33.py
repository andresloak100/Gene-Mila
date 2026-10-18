import numpy as np
from genemila.features.api import Feature, register


@register
class PromoterCpgGcE33(Feature):
    name = "promoter_cpg_gc_e33"
    version = 1
    description = "Standardized promoter GC content and CpG observed/expected ratio per gene."
    rationale = (
        "Promoter GC and CpG content influence transcriptional regulation and chromatin "
        "state, affecting how genes respond to perturbations."
    )
    inputs = ["knowledge:gene_annotation"]
    params = {}
    dim = 2

    _COLS = ("gc_promoter", "cpg_oe_promoter")

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, self.dim), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if not ann:
            return out

        columns = ann.get("columns", [])
        genes = ann.get("genes", {})

        # Locate requested columns
        col_idx = []
        for c in self._COLS:
            if c in columns:
                col_idx.append(columns.index(c))
            else:
                col_idx.append(None)

        if all(ci is None for ci in col_idx):
            return out

        # Build per-gene raw matrix aligned to ctx.genes
        raw = np.full((n_genes, self.dim), np.nan, dtype=float)
        for gi, g in enumerate(ctx.genes):
            vals = genes.get(g)
            if vals is None:
                continue
            for k, ci in enumerate(col_idx):
                if ci is None or ci >= len(vals):
                    continue
                v = vals[ci]
                if v is None:
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv):
                    raw[gi, k] = fv

        # Standardize each column over genes with finite values
        for k in range(self.dim):
            col = raw[:, k]
            mask = np.isfinite(col)
            if not mask.any():
                continue
            mu = col[mask].mean()
            sd = col[mask].std()
            if sd <= 0 or not np.isfinite(sd):
                col[mask] = 0.0
            else:
                col[mask] = (col[mask] - mu) / sd
            raw[:, k] = col

        # Fill missing with 0 (standardized mean)
        raw = np.where(np.isfinite(raw), raw, 0.0)

        # Same per-gene vector for every perturbation
        out[:, :, :] = raw[np.newaxis, :, :]
        return out
