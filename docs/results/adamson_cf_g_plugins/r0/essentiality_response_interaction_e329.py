import numpy as np
from genemila.features.api import Feature, register


@register
class EssentialityResponseInteraction(Feature):
    name = "essentiality_response_interaction_e329"
    version = 1
    description = (
        "For each (p,g): (1 - LOEUF_target) * mean_response_g, where mean_response_g "
        "is the average delta of gene g across training perturbations (leave-one-out)."
    )
    rationale = (
        "Perturbing essential genes (low LOEUF) may cause larger changes in genes that are "
        "themselves broadly responsive across perturbations; this interaction captures that."
    )
    inputs = ["mean_response", "gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = len(perts)
        n_genes = ctx.n_genes

        # mean_response feature: (n, n_genes, 1), leave-one-out per perturbation
        mr = ctx.feature("mean_response", perts, params=None)
        mr = np.asarray(mr, dtype=float).reshape(n, n_genes)

        # Load LOEUF from gene_constraint prior knowledge
        loeuf = np.full(n_genes, np.nan, dtype=float)
        gc = ctx.knowledge("gene_constraint")
        if gc is not None:
            cols = gc.get("columns", [])
            try:
                loeuf_idx = cols.index("oe_lof_upper")
            except ValueError:
                loeuf_idx = None
            genes_tbl = gc.get("genes", {}) or {}
            if loeuf_idx is not None:
                for g, vals in genes_tbl.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None:
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
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        loeuf[gi] = fv

        # Fallback for missing LOEUF: use median of available (neutral-ish), else 1.0
        finite_mask = np.isfinite(loeuf)
        if finite_mask.any():
            fill = float(np.median(loeuf[finite_mask]))
        else:
            fill = 1.0
        loeuf = np.where(finite_mask, loeuf, fill)
        # Clamp to [0, 1] for stability
        loeuf = np.clip(loeuf, 0.0, 1.0)

        out = np.zeros((n, n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if len(t_idx) == 0:
                # No measured target: no essentiality signal, feature is zero
                out[i, :, 0] = 0.0
                continue
            # Average LOEUF across target genes (usually one)
            tl = float(np.mean(loeuf[np.asarray(t_idx, dtype=int)]))
            essentiality = 1.0 - tl
            out[i, :, 0] = essentiality * mr[i, :]

        # Ensure finite values
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
