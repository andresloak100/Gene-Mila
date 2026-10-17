import numpy as np
from genemila.features.api import Feature, register


@register
class TargetKnockdownProxyE14(Feature):
    name = "target_knockdown_proxy_e14"
    version = 1
    description = (
        "For perturbation p, a target-level proxy of knockdown efficiency computed "
        "from control expression of the target gene and its LoF constraint (LOEUF); "
        "the same scalar is assigned to all genes."
    )
    rationale = (
        "Perturbation effect size depends on how strongly the target is knocked down; "
        "high expression or low LoF constraint may indicate stronger knockdown, so a "
        "target-level knockdown proxy can modulate the predicted delta magnitude."
    )
    inputs = ["control_mean", "knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        n_genes = ctx.n_genes
        out = np.zeros((n_perts, n_genes, 1), dtype=float)

        # Precompute control expression proxy (log1p of control mean) per gene.
        ctrl = np.asarray(ctx.control_mean, dtype=float)
        ctrl = np.nan_to_num(ctrl, nan=0.0, posinf=0.0, neginf=0.0)
        # Normalise control expression to [0, 1] via robust min-max.
        cmin = float(np.min(ctrl)) if ctrl.size else 0.0
        cmax = float(np.max(ctrl)) if ctrl.size else 0.0
        if cmax > cmin:
            ctrl_norm = (ctrl - cmin) / (cmax - cmin)
        else:
            ctrl_norm = np.zeros_like(ctrl)

        # Load LoF constraint (LOEUF) knowledge once.
        loeuf = np.full(n_genes, np.nan, dtype=float)
        constraint = None
        try:
            constraint = ctx.knowledge("gene_constraint")
        except Exception:
            constraint = None

        if isinstance(constraint, dict):
            genes_map = constraint.get("genes", {})
            columns = constraint.get("columns", [])
            try:
                loeuf_idx = list(columns).index("oe_lof_upper")
            except ValueError:
                loeuf_idx = None
            if loeuf_idx is not None and isinstance(genes_map, dict):
                for g, vals in genes_map.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None:
                        continue
                    if not isinstance(vals, (list, tuple)) or len(vals) <= loeuf_idx:
                        continue
                    v = vals[loeuf_idx]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv) and fv >= 0.0:
                        loeuf[gi] = fv

        # Inverse LOEUF proxy: lower LOEUF (more constrained) -> larger value.
        # Use 1/(LOEUF + eps); missing -> neutral small value.
        eps = 0.1
        has_loeuf = np.isfinite(loeuf)
        inv_loeuf = np.zeros(n_genes, dtype=float)
        if np.any(has_loeuf):
            raw = 1.0 / (loeuf[has_loeuf] + eps)
            # Normalise to [0, 1] robustly.
            rmin = float(np.min(raw))
            rmax = float(np.max(raw))
            if rmax > rmin:
                inv_loeuf[has_loeuf] = (raw - rmin) / (rmax - rmin)
            else:
                inv_loeuf[has_loeuf] = 0.5

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                # No measured target: neutral value.
                val = 0.5
            else:
                ctrl_vals = np.array([ctrl_norm[j] for j in tgt_idx], dtype=float)
                loeuf_vals = np.array([inv_loeuf[j] for j in tgt_idx], dtype=float)
                # Combine: average of expression proxy and constraint proxy.
                val = 0.5 * float(np.mean(ctrl_vals)) + 0.5 * float(np.mean(loeuf_vals))
            if not np.isfinite(val):
                val = 0.5
            out[i, :, 0] = val

        return out
