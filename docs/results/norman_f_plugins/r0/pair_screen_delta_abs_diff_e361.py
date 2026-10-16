import numpy as np
from genemila.features.api import Feature, register


@register
class PairScreenDeltaAbsDiffE361(Feature):
    name = "pair_screen_delta_abs_diff_e361"
    version = 1
    description = "Absolute difference in signed Replogle screen deltas between the two targets of a pair perturbation; 0 for singles."
    rationale = "Divergent intrinsic target effects may drive non-additive pair responses."
    inputs = ["gene_annotation", "replogle2022_k562"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=np.float64)

        # Get sign-flipped Replogle screen delta per gene (broadcast across all genes)
        # Use the existing feature for consistency.
        try:
            screen = ctx.feature("replogle_delta_signed_e35", ctx.perts, params=None)
            # screen shape: (n_perts, n_genes, 1) presumably
            if screen.ndim == 3:
                screen = screen[:, :, 0]
            # Build a gene -> delta map from training perturbations (single-gene ids)
            delta_by_gene = {}
            for i, p in enumerate(ctx.perts):
                genes = ctx.target_genes(p)
                if len(genes) == 1:
                    g = genes[0]
                    if g not in delta_by_gene:
                        delta_by_gene[g] = float(screen[i].mean())
        except Exception:
            delta_by_gene = {}

        for i, p in enumerate(perts):
            genes = ctx.target_genes(p)
            if len(genes) == 2:
                d1 = delta_by_gene.get(genes[0], 0.0)
                d2 = delta_by_gene.get(genes[1], 0.0)
                out[i, :, 0] = abs(d1 - d2)
            else:
                out[i, :, 0] = 0.0

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
