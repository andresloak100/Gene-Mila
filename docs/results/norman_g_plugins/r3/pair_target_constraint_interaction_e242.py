import numpy as np
from genemila.features.api import Feature, register


@register
class PairTargetConstraintInteractionE242(Feature):
    name = "pair_target_constraint_interaction_e242"
    version = 1
    description = (
        "For each perturbation, combine normalized LoF-intolerance scores (1 - LOEUF) "
        "of its target gene(s) (min or product for pairs, own score for singles) and "
        "multiply by is_target or additive_response, broadcast to all genes."
    )
    rationale = (
        "For pair perturbations the combined LoF intolerance of both targets may "
        "modulate the response beyond the single-target constraint interaction; "
        "dosage sensitivity of both targets can shape the combined effect."
    )
    inputs = ["gene_constraint", "target_genes"]
    params = {"agg": "min", "multiplier": "additive_response"}
    dim = 1

    def _normalized_intolerance(self, ctx):
        """Return dict gene -> normalized LoF-intolerance in [0,1], cached."""
        cache = ctx.cache
        key = "_e242_norm_intol"
        if key in cache:
            return cache[key]

        knowledge = ctx.knowledge("gene_constraint")
        norm = {}
        if knowledge is not None:
            cols = knowledge.get("columns", [])
            genes_tbl = knowledge.get("genes", {})
            # locate LOEUF column (oe_lof_upper)
            oe_idx = None
            for i, c in enumerate(cols):
                if c == "oe_lof_upper":
                    oe_idx = i
                    break
            if oe_idx is not None:
                vals = []
                gene_vals = {}
                for g, row in genes_tbl.items():
                    if not isinstance(row, (list, tuple)) or len(row) <= oe_idx:
                        continue
                    v = row[oe_idx]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if not np.isfinite(fv):
                        continue
                    gene_vals[g] = fv
                    vals.append(fv)
                if vals:
                    arr = np.asarray(vals, dtype=float)
                    lo = np.percentile(arr, 2)
                    hi = np.percentile(arr, 98)
                    if hi <= lo:
                        lo = arr.min()
                        hi = arr.max()
                    span = hi - lo
                    for g, fv in gene_vals.items():
                        if span > 0:
                            clipped = min(max(fv, lo), hi)
                            intol = 1.0 - (clipped - lo) / span
                        else:
                            intol = 0.5
                        norm[g] = float(min(max(intol, 0.0), 1.0))

        cache[key] = norm
        return norm

    def compute(self, ctx, perts, params):
        agg = params.get("agg", "min")
        multiplier = params.get("multiplier", "additive_response")
        norm = self._normalized_intolerance(ctx)

        n_perts = len(perts)
        out = np.zeros((n_perts, ctx.n_genes, 1), dtype=float)

        # Precompute additive_response if needed
        add_resp = None
        if multiplier == "additive_response":
            try:
                add_resp = ctx.feature("additive_response", perts)
            except Exception:
                add_resp = None
            if add_resp is not None:
                add_resp = np.asarray(add_resp, dtype=float)
                if add_resp.ndim == 2:
                    add_resp = add_resp[:, :, None]
                if add_resp.shape[0] != n_perts or add_resp.shape[1] != ctx.n_genes:
                    add_resp = None

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            scores = [norm[g] for g in targets if g in norm]

            if not scores:
                combined = 0.0
            elif len(scores) == 1:
                combined = scores[0]
            else:
                if agg == "product":
                    combined = float(np.prod(scores))
                else:  # min
                    combined = float(np.min(scores))

            if multiplier == "is_target":
                mask = np.zeros(ctx.n_genes, dtype=float)
                for gi in ctx.target_indices(p):
                    if 0 <= gi < ctx.n_genes:
                        mask[gi] = 1.0
                out[i, :, 0] = combined * mask
            else:
                if add_resp is not None:
                    out[i, :, 0] = combined * add_resp[i, :, 0]
                else:
                    # fallback: broadcast combined to all genes
                    out[i, :, 0] = combined

        # ensure finite
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
