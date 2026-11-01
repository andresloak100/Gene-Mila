import numpy as np
from genemila.features.api import Feature, register


@register
class Utr3LengthE69(Feature):
    name = "utr3_length_e69"
    version = 1
    description = "Length of 3' UTR (bp) for gene g from gene_annotation."
    rationale = ("Longer 3' UTRs provide more regulatory sites (miRNA binding sites, "
                 "AU-rich elements) that may buffer/stabilize expression changes under perturbation.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # Load annotation table
        ann = ctx.knowledge("gene_annotation")
        values = np.zeros(n_genes, dtype=float)

        if ann is not None:
            columns = ann.get("columns", [])
            genes_table = ann.get("genes", {}) or {}
            try:
                col_idx = columns.index("utr3_length")
            except ValueError:
                col_idx = None

            if col_idx is not None:
                for gi, g in enumerate(ctx.genes):
                    row = genes_table.get(g)
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
                        values[gi] = fv

        # Same per-gene value for every perturbation row
        out[:, :, 0] = values[None, :]
        return out
