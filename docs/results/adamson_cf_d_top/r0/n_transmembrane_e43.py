import numpy as np
from genemila.features.api import Feature, register


@register
class NTransmembraneE43(Feature):
    name = "n_transmembrane_e43"
    version = 1
    description = "Number of transmembrane segments for gene g from protein_annotation."
    rationale = ("Membrane proteins may be less transcriptionally regulated or more buffered; "
                 "n_transmembrane is unread and may reduce perturbation response magnitude.")
    inputs = ["knowledge:protein_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        vals = np.zeros(n_genes, dtype=float)

        ann = ctx.knowledge("protein_annotation")
        if ann is not None:
            cols = ann.get("columns", [])
            genes = ann.get("genes", {})
            try:
                col_idx = cols.index("n_transmembrane")
            except (ValueError, AttributeError):
                col_idx = None
            if col_idx is not None:
                for g in ctx.genes:
                    row = genes.get(g)
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
                        vals[ctx.gene_index[g]] = fv

        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = vals[None, :]
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
