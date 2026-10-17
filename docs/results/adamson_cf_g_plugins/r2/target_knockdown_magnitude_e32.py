import numpy as np
from genemila.features.api import Feature, register


@register
class TargetKnockdownMagnitudeE32(Feature):
    name = "target_knockdown_magnitude_e32"
    version = 1
    description = ("Target gene control expression and LoF constraint (LOEUF, pLI) "
                   "broadcast to all genes, approximating CRISPRi knockdown strength.")
    rationale = ("CRISPRi efficiency depends on target expression and chromatin/essentiality "
                 "context; high-expression or LoF-intolerant targets may yield stronger "
                 "downstream responses.")
    inputs = ["control_mean", "knowledge"]
    params = {"use_loeuf": True, "use_pli": True}
    dim = 3

    def compute(self, ctx, perts, params):
        use_loeuf = bool(params.get("use_loeuf", True))
        use_pli = bool(params.get("use_pli", True))

        n = len(perts)
        out = np.zeros((n, ctx.n_genes, self.dim), dtype=float)

        # Load constraint table once, cached.
        constraint = None
        if use_loeuf or use_pli:
            if "constraint_bundle" in ctx.cache:
                constraint = ctx.cache["constraint_bundle"]
            else:
                constraint = ctx.knowledge("gene_constraint")
                ctx.cache["constraint_bundle"] = constraint

        oe_idx = pli_idx = None
        if constraint is not None:
            cols = constraint.get("columns", [])
            for j, c in enumerate(cols):
                cl = c.lower()
                if oe_idx is None and ("oe_lof_upper" in cl or "lof_upper" in cl):
                    oe_idx = j
                if pli_idx is None and cl == "pli":
                    pli_idx = j
            if oe_idx is None:
                for j, c in enumerate(cols):
                    if "loeuf" in c.lower():
                        oe_idx = j
                        break
            if pli_idx is None:
                for j, c in enumerate(cols):
                    if c.lower() in ("pli", "p_li", "pli_value"):
                        pli_idx = j
                        break
        cgenes = constraint.get("genes", {}) if constraint is not None else {}

        cm = ctx.control_mean

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                # No measured target: leave zeros (neutral).
                continue
            # Use first target for the broadcast values.
            t = tgt_idx[0]

            # Column 0: control mean expression of the target.
            val_expr = float(cm[t]) if np.isfinite(cm[t]) else 0.0
            out[i, :, 0] = val_expr

            # Constraint values for the target.
            loeuf_val = 0.0
            pli_val = 0.0
            if constraint is not None:
                tgenes = ctx.target_genes(p)
                sym = tgenes[0] if tgenes else None
                if sym is not None and sym in cgenes:
                    vals = cgenes[sym]
                    if use_loeuf and oe_idx is not None and oe_idx < len(vals):
                        v = vals[oe_idx]
                        if v is not None:
                            try:
                                fv = float(v)
                                if np.isfinite(fv):
                                    loeuf_val = fv
                            except (TypeError, ValueError):
                                pass
                    if use_pli and pli_idx is not None and pli_idx < len(vals):
                        v = vals[pli_idx]
                        if v is not None:
                            try:
                                fv = float(v)
                                if np.isfinite(fv):
                                    pli_val = fv
                            except (TypeError, ValueError):
                                pass

            out[i, :, 1] = loeuf_val
            out[i, :, 2] = pli_val

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
