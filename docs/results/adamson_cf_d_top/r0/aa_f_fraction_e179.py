import numpy as np
from genemila.features.api import Feature, register


@register
class AaFFractionE179(Feature):
    name = "aa_f_fraction_e179"
    version = 1
    description = "Fraction of phenylalanine residues in the protein of gene g from gene_annotation."
    rationale = "Phenylalanine content may influence protein complex stability and expression changes."
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is None:
            return out

        genes = ann.get("genes", {})
        columns = ann.get("columns", [])
        try:
            col_idx = list(columns).index("aa_F")
        except ValueError:
            return out

        vals = np.full(n_genes, np.nan, dtype=float)
        for g, gi in ctx.gene_index.items():
            row = genes.get(g)
            if row is None:
                continue
            if col_idx >= len(row):
                continue
            v = row[col_idx]
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv):
                vals[gi] = fv

        # fill missing with column mean (finite) or 0
        finite = np.isfinite(vals)
        if finite.any():
            fill = float(vals[finite].mean())
        else:
            fill = 0.0
        vals = np.where(finite, vals, fill)

        out[:, :, 0] = vals[None, :]
        return out
