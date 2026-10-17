import numpy as np
from genemila.features.api import Feature, register


@register
class EssentialitySelfDeltaInteraction(Feature):
    name = "essentiality_selfdelta_interaction_e234_e249"
    version = 1
    description = "(1 - LOEUF_gene) * target_self_delta_e54"
    rationale = ("Essential genes may be more tightly regulated; their response might depend "
                 "on perturbation strength. Weighting the perturbation self-delta by gene "
                 "essentiality (1 - LOEUF) captures this interaction.")
    inputs = ["knowledge", "feature"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        n_genes = ctx.n_genes

        # Per-gene essentiality weight: (1 - LOEUF) if available, else 0.
        ess = np.zeros(n_genes, dtype=float)
        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            genes = kc.get("genes", {})
            cols = kc.get("columns", [])
            try:
                loeuf_idx = cols.index("oe_lof_upper")
            except (ValueError, AttributeError):
                loeuf_idx = None
            if loeuf_idx is not None:
                for g, vals in genes.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None:
                        continue
                    try:
                        v = vals[loeuf_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        v = float(v)
                    except (TypeError, ValueError):
                        continue
                    if not np.isfinite(v):
                        continue
                    ess[gi] = 1.0 - v

        # target_self_delta_e54 feature: shape (n_perts, n_genes, dim)
        self_delta = ctx.feature("target_self_delta_e54", perts, {})
        self_delta = np.asarray(self_delta, dtype=float)
        if self_delta.ndim == 2:
            self_delta = self_delta[:, :, None]
        sd = self_delta[:, :, 0]

        out = np.zeros((n_perts, n_genes, 1), dtype=float)
        out[:, :, 0] = sd * ess[None, :]
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
