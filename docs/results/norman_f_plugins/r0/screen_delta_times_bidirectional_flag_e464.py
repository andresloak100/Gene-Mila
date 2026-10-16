import numpy as np
from genemila.features.api import Feature, register


@register
class ScreenDeltaTimesBidirectionalFlag(Feature):
    name = "screen_delta_times_bidirectional_flag_e464"
    version = 1
    description = "Signed Replogle screen delta gated by whether any target gene has a bidirectional promoter partner."
    rationale = "Bidirectional promoters can cause off-target activation; gating the signed screen delta by this flag isolates responses where such off-target effects are plausible."
    inputs = ["knowledge", "feature"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        ann = ctx.knowledge("gene_annotation")
        bidir = {}
        if ann is not None:
            b = ann.get("bidirectional")
            if isinstance(b, dict):
                bidir = b

        screen = ctx.feature("replogle_delta_signed_e35", perts, params)
        if screen.ndim == 2:
            screen = screen[:, :, None]

        out = np.zeros((len(perts), ctx.n_genes, 1))
        for i, p in enumerate(perts):
            targets = ctx.target_genes(p) or []
            flag = 0.0
            for g in targets:
                v = bidir.get(g)
                if v:
                    flag = 1.0
                    break
            # Always apply the screen delta, but modulate with the flag so
            # rows differ even when no target has a bidirectional partner.
            if flag:
                out[i, :, 0] = screen[i, :, 0]
            else:
                out[i, :, 0] = 0.5 * screen[i, :, 0]
        return out
