import numpy as np
from genemila.features.api import Feature, register


@register
class CpgOePromoterBinaryE44(Feature):
    name = "cpg_oe_promoter_binary_e44"
    version = 1
    description = "Binary indicator: 1 if cpg_oe_promoter > 0.6 (high CpG observed/expected ratio), else 0."
    rationale = (
        "Genes whose promoters overlap CpG islands (high cpg_oe_promoter) are more likely to be "
        "regulated by methylation and show distinct responses to perturbations."
    )
    inputs = ["knowledge:gene_annotation"]
    params = {"threshold": 0.6}
    dim = 1

    def compute(self, ctx, perts, params):
        threshold = params.get("threshold", 0.6)
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        ka = ctx.knowledge("gene_annotation")
        if ka is None:
            return out

        genes_table = ka.get("genes", {}) if isinstance(ka, dict) else {}
        columns = ka.get("columns", []) if isinstance(ka, dict) else []
        try:
            col_idx = columns.index("cpg_oe_promoter")
        except ValueError:
            col_idx = None

        if col_idx is None:
            return out

        indicator = np.zeros(n_genes, dtype=float)
        for j, g in enumerate(ctx.genes):
            vals = genes_table.get(g)
            if vals is None:
                continue
            try:
                v = vals[col_idx]
            except (IndexError, TypeError):
                continue
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv) and fv > threshold:
                indicator[j] = 1.0

        out[:] = indicator[None, :, None]
        return out
