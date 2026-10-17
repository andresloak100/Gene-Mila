import numpy as np
from genemila.features.api import Feature, register


@register
class TargetIsNuclearE35(Feature):
    name = "target_is_nuclear_e35"
    version = 1
    description = "Binary feature: 1 if the target gene's protein is annotated as localized to the nucleus, else 0."
    rationale = (
        "Proteins in different compartments participate in different regulatory processes. "
        "Targeting a nuclear protein may affect transcription more broadly than targeting a "
        "cytoplasmic protein, so a nuclear-localization indicator helps distinguish such perturbations."
    )
    inputs = ["protein_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("protein_annotation")
        if not ann:
            return out

        columns = ann.get("columns", [])
        genes = ann.get("genes", {})

        # Locate the nucleus flag column.
        try:
            nuc_idx = columns.index("nucleus")
        except ValueError:
            return out

        # Precompute per-gene-column nuclear flag for target genes.
        nuc_flag = np.zeros(ctx.n_genes, dtype=float)
        for g, col_i in ctx.gene_index.items():
            vals = genes.get(g)
            if vals is None:
                continue
            try:
                flag = vals[nuc_idx]
            except (IndexError, TypeError):
                continue
            if flag is None:
                continue
            try:
                f = float(flag)
            except (TypeError, ValueError):
                continue
            if np.isfinite(f):
                nuc_flag[col_i] = 1.0 if f != 0.0 else 0.0

        for i, p in enumerate(perts):
            for ti in ctx.target_indices(p):
                out[i, ti, 0] = nuc_flag[ti]

        return out
