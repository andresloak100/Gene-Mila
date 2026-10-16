import numpy as np
from genemila.features.api import Feature, register


@register
class ScreenDeltaTimesIntronLength(Feature):
    name = "screen_delta_times_intron_length_e419"
    version = 1
    description = "Elementwise product of signed Replogle screen delta (sum over targets) and intron length (kb) of gene g."
    rationale = ("Intron length affects transcription elongation and splicing delay; "
                 "scaling the signed screen delta by intron length may capture "
                 "regulatory complexity or transcriptional delay effects.")
    inputs = ["gene_annotation", "replogle_delta_signed_e35"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        # intron_length_kb per gene, aligned to ctx.genes
        intron = np.zeros(n, dtype=np.float64)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes_ann = ann.get("genes", {})
            columns = ann.get("columns", [])
            try:
                idx = columns.index("intron_length_kb")
            except (ValueError, AttributeError):
                idx = None
            if idx is not None:
                for gi, g in enumerate(ctx.genes):
                    vals = genes_ann.get(g)
                    if vals is None:
                        continue
                    try:
                        v = vals[idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        intron[gi] = fv
        intron = np.nan_to_num(intron, nan=0.0, posinf=0.0, neginf=0.0)

        # signed screen delta feature: shape (len(perts), n_genes, dim)
        screen = ctx.feature("replogle_delta_signed_e35", perts)
        screen = np.asarray(screen, dtype=np.float64)
        if screen.ndim == 2:
            screen = screen[:, :, None]
        screen = np.nan_to_num(screen, nan=0.0, posinf=0.0, neginf=0.0)

        out = screen * intron[None, :, None]
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out.astype(np.float64)
