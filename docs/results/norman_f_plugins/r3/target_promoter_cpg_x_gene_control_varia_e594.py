import numpy as np
from genemila.features.api import Feature, register

@register
class TargetPromoterCpgXGeneControlVariaE594(Feature):
    name = "target_promoter_cpg_x_gene_control_varia_e594"
    version = 1
    description = "Product of mean CpG promoter content across target genes of p and the variance of gene g's control expression."
    rationale = "Promoter CpG influences transcriptional responsiveness, and control variance reflects baseline noise; their interaction may modulate delta."
    inputs = ["control_cells", "knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        # variance of gene g's control expression across control cells
        gene_var = np.var(ctx.control_cells, axis=0).astype(np.float64)

        ann = ctx.knowledge("gene_annotation")
        genes_data = {}
        if ann is not None and isinstance(ann, dict):
            genes_data = ann.get("genes", {}) or {}

        # cpg_oe_promoter is column index 11 per column_units order
        def get_cpg(gene):
            vals = genes_data.get(gene)
            if vals is None:
                return np.nan
            try:
                v = vals[11]
            except Exception:
                return np.nan
            if v is None:
                return np.nan
            try:
                f = float(v)
            except Exception:
                return np.nan
            return f

        out = np.zeros((len(perts), n_genes, 1), dtype=np.float64)
        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            vals = [get_cpg(g) for g in targets]
            vals = [v for v in vals if np.isfinite(v)]
            if len(vals) > 0:
                mean_cpg = float(np.mean(vals))
            else:
                mean_cpg = 0.0
            out[i, :, 0] = mean_cpg * gene_var
        out[~np.isfinite(out)] = 0.0
        return out
