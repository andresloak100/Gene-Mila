import numpy as np
from genemila.features.api import Feature, register


@register
class PromoterCpgGcFeaturesE61(Feature):
    name = "promoter_cpg_gc_features_e61"
    version = 1
    description = (
        "Per-gene standardized promoter GC content (gc_promoter) and CpG observed/expected "
        "ratio (cpg_oe_promoter) from gene_annotation."
    )
    rationale = (
        "Promoter CpG density and GC content affect transcriptional regulation and chromatin "
        "state, potentially explaining residual variation in perturbation responses."
    )
    inputs = ["gene_annotation"]
    params = {}
    dim = 2

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, self.dim), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        cols = None
        if ann is not None:
            cols = ann.get("columns") or []
        if cols is None:
            cols = []

        try:
            i_gc = cols.index("gc_promoter")
        except ValueError:
            i_gc = None
        try:
            i_cpg = cols.index("cpg_oe_promoter")
        except ValueError:
            i_cpg = None

        gc_vals = np.full(n_genes, np.nan, dtype=float)
        cpg_vals = np.full(n_genes, np.nan, dtype=float)

        genes_tbl = ann.get("genes") if isinstance(ann, dict) else None
        if isinstance(genes_tbl, dict):
            for gi, g in enumerate(ctx.genes):
                row = genes_tbl.get(g)
                if row is None:
                    continue
                if i_gc is not None and i_gc < len(row):
                    v = row[i_gc]
                    if v is not None:
                        try:
                            fv = float(v)
                            if np.isfinite(fv):
                                gc_vals[gi] = fv
                        except (TypeError, ValueError):
                            pass
                if i_cpg is not None and i_cpg < len(row):
                    v = row[i_cpg]
                    if v is not None:
                        try:
                            fv = float(v)
                            if np.isfinite(fv):
                                cpg_vals[gi] = fv
                        except (TypeError, ValueError):
                            pass

        def _standardize(a):
            out_a = np.zeros_like(a)
            mask = np.isfinite(a)
            if mask.any():
                vals = a[mask]
                mu = vals.mean()
                sd = vals.std()
                if sd > 1e-12:
                    out_a[mask] = (vals - mu) / sd
                # else leave zeros
            return out_a

        gc_std = _standardize(gc_vals)
        cpg_std = _standardize(cpg_vals)

        out[:, :, 0] = gc_std[np.newaxis, :]
        out[:, :, 1] = cpg_std[np.newaxis, :]

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
