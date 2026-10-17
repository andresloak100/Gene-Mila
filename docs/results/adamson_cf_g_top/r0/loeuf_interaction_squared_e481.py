import numpy as np
from genemila.features.api import Feature, register


@register
class LoeufInteractionSquaredE481(Feature):
    name = "loeuf_interaction_squared_e481"
    version = 1
    description = (
        "Nonlinear (squared) LOEUF interaction: (1 - LOEUF_target)^2 * (1 - LOEUF_gene)^2 "
        "for each (perturbation, gene) pair."
    )
    rationale = (
        "Essentiality may act with threshold/saturation effects; squaring the existing "
        "linear LOEUF interaction emphasizes strongly LoF-intolerant genes and targets."
    )
    inputs = ["knowledge"]
    params = {"transform": "square"}
    dim = 1

    def compute(self, ctx, perts, params):
        transform = params.get("transform", "square")
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # Load gnomAD LoF constraint knowledge; column 'oe_lof_upper' is LOEUF.
        constraint = ctx.knowledge("gene_constraint")
        loeuf = np.full(n_genes, np.nan, dtype=float)
        if constraint is not None:
            genes = constraint.get("genes", {}) or {}
            columns = constraint.get("columns", []) or []
            try:
                loeuf_idx = columns.index("oe_lof_upper")
            except ValueError:
                loeuf_idx = None
            if loeuf_idx is not None:
                for g, vals in genes.items():
                    j = ctx.gene_index.get(g)
                    if j is None:
                        continue
                    if vals is None:
                        continue
                    try:
                        v = vals[loeuf_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        loeuf[j] = float(v)
                    except (TypeError, ValueError):
                        continue

        # Missing LOEUF -> neutral value (LOEUF = 1 => 1 - LOEUF = 0).
        loeuf = np.where(np.isfinite(loeuf), loeuf, 1.0)
        # Clip to [0, 1] so (1 - LOEUF) is a proper essentiality weight.
        loeuf = np.clip(loeuf, 0.0, 1.0)
        ess = 1.0 - loeuf  # (n_genes,)

        if transform == "log":
            ess = np.log1p(ess)
        elif transform == "square":
            ess = ess * ess
        # else linear

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if len(tgt_idx) == 0:
                target_ess = 1.0  # neutral weight if target unmeasured
            else:
                target_ess = float(np.mean(ess[tgt_idx]))
            out[i, :, 0] = target_ess * ess

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
