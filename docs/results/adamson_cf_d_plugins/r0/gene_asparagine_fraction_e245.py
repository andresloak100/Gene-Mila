import numpy as np
from genemila.features.api import Feature, register


@register
class GeneAsparagineFraction(Feature):
    name = "gene_asparagine_fraction_e245"
    version = 1
    description = "Fraction of asparagine residues in the protein of gene g."
    rationale = ("Asparagine content may mark mitochondrial targeting or metabolic "
                 "function; mitochondrial proteins in particular may show distinct "
                 "expression responses to perturbation.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if not ann:
            return out

        genes_map = ann.get("genes") or {}
        columns = ann.get("columns") or []
        try:
            col_idx = columns.index("aa_N")
        except ValueError:
            return out

        # Build a per-gene value vector aligned to ctx.genes
        vals = np.zeros(ctx.n_genes, dtype=float)
        for g, gi in ctx.gene_index.items():
            row = genes_map.get(g)
            if row is None:
                continue
            try:
                v = row[col_idx]
            except (IndexError, TypeError):
                continue
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv):
                vals[gi] = fv

        out[:, :, 0] = vals[None, :]
        return out
