import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveResponseXTargetConstraint(Feature):
    name = "additive_response_x_target_constraint_e302"
    version = 1
    description = "Product of additive_response and a normalized LoF-intolerance score of the target gene(s)."
    rationale = "LoF-intolerant targets are more essential; their perturbation may yield stronger downstream effects."
    inputs = ["control_cells", "knowledge"]
    params = {}
    dim = 1

    def _constraint_score(self, ctx):
        cache = ctx.cache
        if "e302_score" in cache:
            return cache["e302_score"]

        n = ctx.n_genes
        raw = np.full(n, np.nan, dtype=float)

        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            cols = list(kc.get("columns", []))
            genes = kc.get("genes", {}) or {}
            try:
                oe_idx = cols.index("oe_lof_upper")
            except ValueError:
                oe_idx = None
            try:
                pli_idx = cols.index("pLI")
            except ValueError:
                pli_idx = None

            for g, gi in ctx.gene_index.items():
                vals = genes.get(g)
                if not vals:
                    continue
                loeuf = None
                pli = None
                if oe_idx is not None and oe_idx < len(vals):
                    loeuf = vals[oe_idx]
                if pli_idx is not None and pli_idx < len(vals):
                    pli = vals[pli_idx]
                score = None
                if loeuf is not None:
                    try:
                        lf = float(loeuf)
                        if np.isfinite(lf):
                            score = 1.0 - lf
                    except (TypeError, ValueError):
                        pass
                if score is None and pli is not None:
                    try:
                        pl = float(pli)
                        if np.isfinite(pl):
                            score = pl
                    except (TypeError, ValueError):
                        pass
                if score is not None:
                    raw[gi] = score

        # Normalize over genes with finite scores
        finite = np.isfinite(raw)
        if finite.any():
            lo = raw[finite].min()
            hi = raw[finite].max()
            if hi > lo:
                norm = (raw - lo) / (hi - lo)
            else:
                norm = np.where(finite, 0.5, np.nan)
        else:
            norm = raw
        # Fill missing with median of finite (or 0.5)
        if finite.any():
            fill = float(np.nanmedian(norm[finite]))
        else:
            fill = 0.5
        norm = np.where(np.isfinite(norm), norm, fill)
        cache["e302_score"] = norm
        return norm

    def compute(self, ctx, perts, params):
        score = self._constraint_score(ctx)
        add = ctx.feature("additive_response", perts)
        add = np.asarray(add, dtype=float)
        if add.ndim == 3:
            add = add[:, :, 0]
        elif add.ndim == 1:
            add = add.reshape(len(perts), -1)

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            idx = ctx.target_indices(p)
            if idx:
                s = float(np.mean(score[idx]))
            else:
                s = 0.5
            out[i, :, 0] = add[i] * s
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
