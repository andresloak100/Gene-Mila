import numpy as np
from genemila.features.api import Feature, register

@register
class AdditiveTimesIntronLengthE443(Feature):
    name = "additive_times_intron_length_e443"
    version = 1
    description = "Elementwise product of additive_response and intron_length_kb of gene g."
    rationale = "Longer introns may delay or alter transcriptional response, interacting with perturbation strength."
    inputs = ["gene_annotation", "additive_response"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1), dtype=np.float64)

        ann = ctx.knowledge("gene_annotation")
        intron = np.zeros(ctx.n_genes, dtype=np.float64)
        if ann is not None:
            genes_ann = ann.get("genes", {})
            columns = ann.get("columns", [])
            idx = None
            if "intron_length_kb" in columns:
                idx = columns.index("intron_length_kb")
            elif "intron_length" in columns:
                idx = columns.index("intron_length")
            if idx is not None:
                for gi, g in enumerate(ctx.genes):
                    vals = genes_ann.get(g)
                    if vals is not None:
                        v = vals[idx]
                        if v is not None:
                            try:
                                fv = float(v)
                                if np.isfinite(fv):
                                    intron[gi] = fv
                            except (TypeError, ValueError):
                                pass

        additive = ctx.feature("additive_response", perts)
        additive = np.asarray(additive, dtype=np.float64)
        if additive.ndim == 2:
            additive = additive[:, :, None]
        elif additive.ndim == 1:
            additive = additive[:, None, None]

        out[:, :, 0] = additive[:, :, 0] * intron[None, :]
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
