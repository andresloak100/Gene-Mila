import numpy as np
from genemila.features.api import Feature, register


@register
class NTssWithin100kbE118(Feature):
    name = "n_tss_within_100kb_e118"
    version = 1
    description = "Number of TSS within 100kb of gene g's TSS from gene_annotation."
    rationale = ("Dense TSS regions may have overlapping regulatory elements that buffer "
                 "expression changes; n_tss_within_100kb is an unread gene_annotation column.")
    inputs = ["gene_annotation"]
    params = {"missing_value": 0.0}
    dim = 1

    def compute(self, ctx, perts, params):
        missing = float(params.get("missing_value", 0.0))
        ann = ctx.knowledge("gene_annotation")

        col = "n_tss_within_100kb"
        values = None
        if isinstance(ann, dict):
            cols = ann.get("columns")
            genes_tbl = ann.get("genes")
            if isinstance(cols, (list, tuple)) and col in cols and isinstance(genes_tbl, dict):
                idx = list(cols).index(col)
                values = {}
                for sym, row in genes_tbl.items():
                    try:
                        v = row[idx]
                    except (IndexError, TypeError):
                        v = None
                    if v is None:
                        v = missing
                    try:
                        v = float(v)
                    except (TypeError, ValueError):
                        v = missing
                    if not np.isfinite(v):
                        v = missing
                    values[sym] = v

        out = np.full((len(perts), ctx.n_genes, 1), missing, dtype=float)
        if values is not None:
            for g_i, sym in enumerate(ctx.genes):
                if sym in values:
                    out[:, g_i, 0] = values[sym]
        return out
