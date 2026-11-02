import numpy as np
from genemila.features.api import Feature, register


@register
class IntronLengthKbDirectE88(Feature):
    name = "intron_length_kb_direct_e88"
    version = 1
    description = "Continuous feature: intron_length_kb from gene_annotation for gene g."
    rationale = (
        "Genes with longer introns have lower transcriptional responsiveness, "
        "leading to smaller perturbation effects."
    )
    inputs = ["gene_annotation"]
    params = {"column": "intron_length_kb"}
    dim = 1

    def compute(self, ctx, perts, params):
        column = params.get("column", "intron_length_kb")
        ann = ctx.knowledge("gene_annotation")

        vals = np.zeros(ctx.n_genes, dtype=float)
        if ann is not None:
            genes = ann.get("genes", {})
            columns = ann.get("columns", [])
            try:
                col_idx = columns.index(column)
            except (ValueError, AttributeError):
                col_idx = None

            for gi, g in enumerate(ctx.genes):
                entry = genes.get(g)
                if entry is None:
                    continue
                v = None
                if isinstance(entry, dict):
                    v = entry.get(column)
                elif isinstance(entry, (list, tuple)) and col_idx is not None:
                    if col_idx < len(entry):
                        v = entry[col_idx]
                if v is None:
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv):
                    vals[gi] = fv

        out = np.empty((len(perts), ctx.n_genes, 1), dtype=float)
        out[:, :, 0] = vals[np.newaxis, :]
        return out
