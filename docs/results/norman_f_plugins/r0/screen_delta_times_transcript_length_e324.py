import numpy as np
from genemila.features.api import Feature, register

@register
class ScreenDeltaTimesTranscriptLength(Feature):
    name = "screen_delta_times_transcript_length_e324"
    version = 1
    description = "Elementwise product of replogle_delta_signed_e35 and transcript length of gene g."
    rationale = "Transcript length may modulate how the signed CRISPRi screen delta transfers to CRISPRa responses."
    inputs = ["knowledge", "feature"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        # transcript length per gene, in bundle column order
        tlen = np.zeros(n, dtype=np.float64)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            cols = ann.get("columns", [])
            try:
                idx = cols.index("transcript_length")
            except ValueError:
                idx = 3  # fallback: documented order
            genes = ann.get("genes", {})
            for g, col in ctx.gene_index.items():
                vals = genes.get(g)
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
                    tlen[col] = fv
        # avoid non-finite
        tlen = np.where(np.isfinite(tlen), tlen, 0.0)

        base = ctx.feature("replogle_delta_signed_e35", perts)
        base = np.asarray(base, dtype=np.float64)
        if base.ndim == 2:
            base = base[:, :, None]
        # base shape (len(perts), n_genes, dim_b)
        out = np.zeros((len(perts), n, 1), dtype=np.float64)
        db = base.shape[2]
        for j in range(db):
            out[:, :, 0] += base[:, :, j] * tlen[None, :]
        out = np.where(np.isfinite(out), out, 0.0)
        return out
