import numpy as np
from genemila.features.api import Feature, register


@register
class ScreenDeltaTimesNExonsE454(Feature):
    name = "screen_delta_times_n_exons_e454"
    version = 1
    description = "Elementwise product of replogle_delta_signed_e35 and n_exons of gene g."
    rationale = "Exon count influences splicing and transcriptional response; interacting it with the signed screen delta may capture gene-specific response modulation."
    inputs = ["knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        ann = ctx.knowledge("gene_annotation")
        n_exons = np.zeros(n_genes, dtype=float)
        if ann is not None:
            genes = ann.get("genes", {})
            cols = ann.get("columns", [])
            try:
                idx = cols.index("n_exons")
            except ValueError:
                idx = None
            if idx is not None:
                for g, gi in ctx.gene_index.items():
                    vals = genes.get(g)
                    if vals is not None:
                        v = vals[idx]
                        if v is not None:
                            n_exons[gi] = float(v)

        # signed screen delta per perturbation row
        screen = ctx.feature("replogle_delta_signed_e35", perts)
        screen = np.asarray(screen, dtype=float)
        if screen.ndim == 3:
            screen = screen[:, :, 0]
        screen = np.nan_to_num(screen, nan=0.0, posinf=0.0, neginf=0.0)

        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = screen * n_exons[None, :]
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
