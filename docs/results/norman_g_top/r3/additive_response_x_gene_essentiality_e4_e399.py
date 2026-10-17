import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveResponseXGeneEssentialityE4E399(Feature):
    name = "additive_response_x_gene_essentiality_e4_e399"
    version = 1
    description = ("Product of additive_response and a per-gene essentiality score "
                   "(1 - LOEUF, or pLI if LOEUF missing).")
    rationale = ("Essential genes may be more tightly regulated and show larger changes "
                 "when their regulators are perturbed; a multiplicative interaction between "
                 "the additive baseline and gene essentiality may improve predictions.")
    inputs = ["control_mean", "knowledge"]
    params = {}
    dim = 1

    def _essentiality(self, ctx):
        cache = ctx.cache
        key = "_e399_essentiality"
        if key in cache:
            return cache[key]
        ess = np.zeros(ctx.n_genes, dtype=float)
        gc = ctx.knowledge("gene_constraint")
        if gc is not None:
            genes = gc.get("genes", {}) or {}
            cols = gc.get("columns", []) or []
            try:
                i_loeuf = cols.index("oe_lof_upper")
            except ValueError:
                i_loeuf = None
            try:
                i_pli = cols.index("pLI")
            except ValueError:
                i_pli = None
            for g, idx in ctx.gene_index.items():
                vals = genes.get(g)
                if vals is None:
                    continue
                score = np.nan
                if i_loeuf is not None and i_loeuf < len(vals):
                    v = vals[i_loeuf]
                    if v is not None:
                        try:
                            fv = float(v)
                            if np.isfinite(fv):
                                score = 1.0 - fv
                        except (TypeError, ValueError):
                            pass
                if not np.isfinite(score) and i_pli is not None and i_pli < len(vals):
                    v = vals[i_pli]
                    if v is not None:
                        try:
                            fv = float(v)
                            if np.isfinite(fv):
                                score = fv
                        except (TypeError, ValueError):
                            pass
                if np.isfinite(score):
                    ess[idx] = score
        # normalize to [0,1]
        lo = ess.min()
        hi = ess.max()
        if hi > lo:
            ess = (ess - lo) / (hi - lo)
        else:
            ess = np.zeros_like(ess)
        ess = np.clip(ess, 0.0, 1.0)
        ess = np.nan_to_num(ess, nan=0.0, posinf=0.0, neginf=0.0)
        cache[key] = ess
        return ess

    def compute(self, ctx, perts, params):
        ess = self._essentiality(ctx)
        add = ctx.feature("additive_response", perts, params=None)
        add = np.asarray(add, dtype=float)
        if add.ndim == 3:
            add = add[:, :, 0]
        elif add.ndim == 1:
            add = add[:, None]
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        out[:, :, 0] = add * ess[None, :]
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
