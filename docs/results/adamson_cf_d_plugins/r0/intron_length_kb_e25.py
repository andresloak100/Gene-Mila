import numpy as np
from genemila.features.api import Feature, register

@register
class IntronLengthKbE25(Feature):
    name = "intron_length_kb_e25"
    version = 1
    description = "Total intron length in kb for gene g, from gene_annotation."
    rationale = ("Longer genes may have slower transcription or more complex regulation, "
                 "dampening the magnitude of expression changes after perturbation.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is None:
            return out

        genes_tbl = ann.get("genes", {}) or {}
        cols = ann.get("columns", []) or []
        try:
            col_idx = cols.index("intron_length_kb")
        except ValueError:
            col_idx = None

        # Build a gene-side vector aligned to ctx.genes
        vals = np.zeros(ctx.n_genes, dtype=float)
        for j, g in enumerate(ctx.genes):
            row = genes_tbl.get(g)
            if row is None:
                continue
            if col_idx is not None:
                v = row[col_idx]
            else:
                # fallback: assume the documented fixed column position (index 7)
                v = row[7] if len(row) > 7 else None
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv):
                vals[j] = fv

        # Same gene-side value for every perturbation row
        out[:, :, 0] = vals[None, :]
        return out
