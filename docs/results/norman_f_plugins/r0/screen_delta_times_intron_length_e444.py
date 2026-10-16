import numpy as np
from genemila.features.api import Feature, register


@register
class ScreenDeltaTimesIntronLengthE444(Feature):
    name = "screen_delta_times_intron_length_e444"
    version = 1
    description = "Elementwise product of replogle_delta_signed_e35 and intron_length_kb of gene g."
    rationale = "Intron length may affect CRISPRa response efficiency and interaction with screen-derived effect."
    inputs = ["knowledge", "feature"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1), dtype=np.float64)

        # intron_length_kb per gene (column index 7 in genes[symbol] values)
        anno = ctx.knowledge("gene_annotation")
        intron = np.zeros(ctx.n_genes, dtype=np.float64)
        if anno is not None and "genes" in anno:
            genes = anno["genes"]
            for gi, g in enumerate(ctx.genes):
                vals = genes.get(g)
                if vals is None:
                    continue
                try:
                    v = vals[7]
                except Exception:
                    continue
                if v is None:
                    continue
                try:
                    fv = float(v)
                except Exception:
                    continue
                if np.isfinite(fv):
                    intron[gi] = fv

        # replogle_delta_signed_e35 feature: shape (n, n_genes, dim)
        try:
            rep = ctx.feature("replogle_delta_signed_e35", perts, params=None)
        except Exception:
            rep = None

        if rep is None:
            return out

        rep = np.asarray(rep, dtype=np.float64)
        if rep.ndim == 2:
            rep = rep[:, :, None]
        if rep.shape[0] != n or rep.shape[1] != ctx.n_genes:
            return out

        rep0 = rep[:, :, 0]

        # product
        out[:, :, 0] = rep0 * intron[None, :]

        # ensure finite
        bad = ~np.isfinite(out)
        if bad.any():
            out[bad] = 0.0

        return out
