import numpy as np
from genemila.features.api import Feature, register


@register
class Utr3LengthE56(Feature):
    name = "utr3_length_e56"
    version = 1
    description = "Length of 3' UTR for gene g from gene_annotation (log1p transformed)."
    rationale = (
        "3' UTR length correlates with post-transcriptional regulatory complexity "
        "(miRNA/RBP binding sites), which may modulate how gene expression responds "
        "to perturbations."
    )
    inputs = ["gene_annotation"]
    params = {"transform": "log1p"}
    dim = 1

    def compute(self, ctx, perts, params):
        transform = params.get("transform", "log1p")
        n_genes = ctx.n_genes

        # Default vector: zeros for genes without annotation.
        base = np.zeros(n_genes, dtype=float)

        ka = ctx.knowledge("gene_annotation")
        if ka is not None:
            columns = ka.get("columns", [])
            genes = ka.get("genes", {}) or {}
            try:
                col_idx = columns.index("utr3_length")
            except ValueError:
                col_idx = None

            if col_idx is not None:
                for g, col in ctx.gene_index.items():
                    vals = genes.get(g)
                    if vals is None:
                        continue
                    try:
                        v = vals[col_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        v = float(v)
                    except (TypeError, ValueError):
                        continue
                    if not np.isfinite(v):
                        continue
                    base[col] = v

        if transform == "log1p":
            base = np.log1p(np.maximum(base, 0.0))
        elif transform == "log":
            base = np.log1p(np.maximum(base, 0.0))
        # else raw

        base = np.nan_to_num(base, nan=0.0, posinf=0.0, neginf=0.0)
        out = np.tile(base[None, :, None], (len(perts), 1, 1))
        return out
