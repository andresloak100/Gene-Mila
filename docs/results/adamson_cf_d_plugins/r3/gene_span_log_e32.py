import numpy as np
from genemila.features.api import Feature, register

@register
class GeneSpanLogE32(Feature):
    name = "gene_span_log_e32"
    version = 1
    description = "Log10 of gene_span_kb for gene g (plus 1)."
    rationale = "Longer genes have more regulatory complexity and are less likely to change expression upon perturbation."
    inputs = ["knowledge:gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        out = np.zeros((n_perts, ctx.n_genes, 1), dtype=float)

        ka = ctx.knowledge("gene_annotation")
        if ka is None:
            return out

        genes_map = ka.get("genes", {}) or {}
        columns = ka.get("columns", []) or []
        try:
            span_idx = columns.index("gene_span_kb")
        except ValueError:
            return out

        vals = np.zeros(ctx.n_genes, dtype=float)
        for j, g in enumerate(ctx.genes):
            row = genes_map.get(g)
            if row is None:
                continue
            if span_idx >= len(row):
                continue
            v = row[span_idx]
            if v is None:
                continue
            try:
                v = float(v)
            except (TypeError, ValueError):
                continue
            if not np.isfinite(v):
                continue
            vals[j] = np.log10(v + 1.0)

        out[:, :, 0] = vals[None, :]
        return out
