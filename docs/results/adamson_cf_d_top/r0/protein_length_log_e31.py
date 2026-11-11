import numpy as np
from genemila.features.api import Feature, register


@register
class ProteinLengthLogE31(Feature):
    name = "protein_length_log_e31"
    version = 1
    description = "Log10 of protein length for gene g from protein_annotation."
    rationale = ("Longer proteins require more translational resources; their mRNAs may be "
                 "buffered against perturbations, attenuating responses.")
    inputs = ["protein_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        vals = np.zeros(n_genes, dtype=float)

        ann = ctx.knowledge("protein_annotation")
        if ann is not None:
            genes = ann.get("genes", {})
            cols = ann.get("columns", [])
            try:
                idx = cols.index("protein_length")
            except ValueError:
                idx = 0
            for g, colvals in genes.items():
                gi = ctx.gene_index.get(g)
                if gi is None or colvals is None:
                    continue
                if idx >= len(colvals):
                    continue
                v = colvals[idx]
                if v is None:
                    continue
                try:
                    v = float(v)
                except (TypeError, ValueError):
                    continue
                if not np.isfinite(v) or v <= 0:
                    continue
                vals[gi] = np.log10(v)

        out = np.empty((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = vals[None, :]
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
