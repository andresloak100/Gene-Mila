import numpy as np
from genemila.features.api import Feature, register


@register
class ScreenDeltaTimesUtr5Length(Feature):
    name = "screen_delta_times_utr5_length_e456"
    version = 1
    description = "Elementwise product of replogle_delta_signed_e35 and utr5_length of gene g."
    rationale = ("5' UTR length influences translational efficiency; multiplying the "
                 "signed screen delta by utr5_length captures gene-specific modulation "
                 "of the perturbation response.")
    inputs = ["knowledge", "replogle_delta_signed_e35"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes

        # --- utr5_length per gene column ---
        utr5 = np.zeros(n_genes, dtype=np.float64)
        ka = ctx.knowledge("gene_annotation")
        if ka is not None:
            genes_block = ka.get("genes", {}) if isinstance(ka, dict) else {}
            cols = ka.get("columns", []) if isinstance(ka, dict) else []
            # locate utr5_length column index
            try:
                u_idx = cols.index("utr5_length")
            except (ValueError, AttributeError):
                u_idx = None
            if u_idx is not None:
                for gi, g in enumerate(ctx.genes):
                    vals = genes_block.get(g)
                    if vals is None:
                        continue
                    try:
                        v = vals[u_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is not None:
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv):
                            utr5[gi] = fv
        # replace any non-finite with 0
        utr5 = np.where(np.isfinite(utr5), utr5, 0.0)

        # --- signed screen delta feature ---
        screen = ctx.feature("replogle_delta_signed_e35", perts)
        # screen shape (n_perts, n_genes, 1)
        screen = np.asarray(screen, dtype=np.float64)
        if screen.ndim == 3:
            screen = screen[:, :, 0]
        elif screen.ndim == 2:
            pass
        else:
            screen = screen.reshape(len(perts), n_genes)

        out = screen * utr5[None, :]
        out = np.where(np.isfinite(out), out, 0.0)
        return out[:, :, None]
