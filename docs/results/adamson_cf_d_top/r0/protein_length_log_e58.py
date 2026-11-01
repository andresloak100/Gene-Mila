import numpy as np
from genemila.features.api import Feature, register


@register
class ProteinLengthLogE58(Feature):
    name = "protein_length_log_e58"
    version = 1
    description = "Log-transformed protein length of gene g from protein_annotation."
    rationale = (
        "Protein length affects translation efficiency and degradation, potentially "
        "altering steady-state mRNA levels after perturbation."
    )
    inputs = ["protein_annotation"]
    params = {"transform": "log1p"}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        vec = np.full(n_genes, np.nan, dtype=float)

        ann = ctx.knowledge("protein_annotation")
        if ann is not None:
            columns = ann.get("columns", [])
            try:
                pl_idx = columns.index("protein_length")
            except ValueError:
                pl_idx = None
            genes_tbl = ann.get("genes", {}) or {}
            if pl_idx is not None:
                for g, vals in genes_tbl.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None:
                        continue
                    if vals is None or pl_idx >= len(vals):
                        continue
                    v = vals[pl_idx]
                    if v is None:
                        continue
                    try:
                        v = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(v) and v >= 0:
                        vec[gi] = v

        # log1p transform on valid entries; invalid -> 0
        valid = np.isfinite(vec)
        out_vec = np.zeros(n_genes, dtype=float)
        out_vec[valid] = np.log1p(vec[valid])

        out = np.empty((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = out_vec[None, :]
        return out
