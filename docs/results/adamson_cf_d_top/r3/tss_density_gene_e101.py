import numpy as np
from genemila.features.api import Feature, register


@register
class TssDensityGeneE101(Feature):
    name = "tss_density_gene_e101"
    version = 1
    description = "Number of TSS within 100kb of each gene's TSS (log-transformed), broadcast across perturbations."
    rationale = "TSS density reflects regulatory complexity; genes in dense regions may have more enhancer interactions and thus larger perturbation responses."
    inputs = ["gene_annotation"]
    params = {"log_transform": True}
    dim = 1

    def compute(self, ctx, perts, params):
        log_transform = params.get("log_transform", True)
        n_genes = ctx.n_genes

        values = np.full(n_genes, np.nan, dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            cols = ann.get("columns", [])
            genes_tbl = ann.get("genes", {})
            if "n_tss_within_100kb" in cols:
                col_idx = cols.index("n_tss_within_100kb")
                for g, row in genes_tbl.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None:
                        continue
                    if row is None or col_idx >= len(row):
                        continue
                    val = row[col_idx]
                    if val is None:
                        continue
                    try:
                        val = float(val)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(val):
                        values[gi] = val

        # Impute missing with median of observed values.
        observed = np.isfinite(values)
        if observed.any():
            median_val = float(np.median(values[observed]))
        else:
            median_val = 0.0
        values[~observed] = median_val

        if log_transform:
            values = np.log1p(np.maximum(values, 0.0))

        values = np.nan_to_num(values, nan=0.0, posinf=0.0, neginf=0.0)

        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = values[np.newaxis, :]
        return out
