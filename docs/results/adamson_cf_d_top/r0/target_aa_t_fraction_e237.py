import numpy as np
from genemila.features.api import Feature, register


@register
class TargetAaTFractionE237(Feature):
    name = "target_aa_t_fraction_e237"
    version = 1
    description = "Fraction of threonine residues in the protein of the targeted gene p, broadcast to all genes g."
    rationale = "Threonine phosphorylation is a key signaling modification; perturbing threonine-rich proteins may cause larger expression changes."
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is None:
            return out

        genes_ann = ann.get("genes", {}) or {}
        columns = ann.get("columns", []) or []
        try:
            t_idx = columns.index("aa_T")
        except ValueError:
            return out

        # Map gene symbol -> aa_T value (may be null)
        aa_t = {}
        for sym, vals in genes_ann.items():
            if vals is None or t_idx >= len(vals):
                continue
            v = vals[t_idx]
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv):
                aa_t[sym] = fv

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            if not tg:
                continue
            vals = [aa_t[g] for g in tg if g in aa_t]
            if not vals:
                continue
            out[i, :, 0] = float(np.mean(vals))

        return out
