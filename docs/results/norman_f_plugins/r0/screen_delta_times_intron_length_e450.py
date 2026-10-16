import numpy as np
from genemila.features.api import Feature, register

@register
class ScreenDeltaTimesIntronLengthE450(Feature):
    name = "screen_delta_times_intron_length_e450"
    version = 1
    description = "Elementwise product of replogle_delta_signed_e35 and intron_length_kb of gene g."
    rationale = "Intron length affects transcriptional kinetics and response scaling."
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        n_genes = ctx.n_genes
        out = np.zeros((n_perts, n_genes, 1), dtype=np.float64)

        ann = ctx.knowledge("gene_annotation")
        if ann is None:
            return out
        genes_ann = ann.get("genes", {})
        columns = ann.get("columns", [])
        try:
            intron_col = columns.index("intron_length_kb")
        except ValueError:
            return out

        # Precompute intron length per gene in bundle order
        intron = np.full(n_genes, np.nan, dtype=np.float64)
        for gi, g in enumerate(ctx.genes):
            vals = genes_ann.get(g)
            if vals is not None and intron_col < len(vals):
                v = vals[intron_col]
                if v is not None:
                    intron[gi] = float(v)
        # Replace NaN with 0
        intron = np.where(np.isfinite(intron), intron, 0.0)

        # Get signed replogle delta feature
        repl = ctx.feature("replogle_delta_signed_e35", perts)
        # repl shape: (n_perts, n_genes, 1) or (n_perts, n_genes)
        if repl.ndim == 3:
            repl = repl[:, :, 0]
        repl = np.where(np.isfinite(repl), repl, 0.0)

        out[:, :, 0] = repl * intron[None, :]
        out = np.where(np.isfinite(out), out, 0.0)
        return out
