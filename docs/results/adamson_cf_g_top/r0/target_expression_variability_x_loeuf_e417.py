import numpy as np
from genemila.features.api import Feature, register


@register
class TargetExpressionVariabilityXLoeuf(Feature):
    name = "target_expression_variability_x_loeuf_e417"
    version = 1
    description = (
        "Product of the perturbation target's control expression coefficient of "
        "variation and (1 - LOEUF_target), broadcast across all genes."
    )
    rationale = (
        "The effect of target expression variability on downstream responses may "
        "depend on target essentiality: highly variable essential targets can have "
        "larger regulatory impact. Scaling variability by (1 - LOEUF) weights "
        "LoF-intolerant (essential) targets more heavily."
    )
    inputs = ["control_cells", "gene_annotation", "gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        n_genes = ctx.n_genes
        out = np.zeros((n_perts, n_genes, 1), dtype=float)

        # --- target expression variability (CV) per perturbation target ---
        # Mean and std across control cells per gene.
        ctrl = ctx.control_cells
        if ctrl is None or ctrl.shape[0] == 0:
            ctrl_mean = np.zeros(n_genes, dtype=float)
            ctrl_std = np.zeros(n_genes, dtype=float)
        else:
            ctrl_mean = np.nanmean(ctrl, axis=0)
            ctrl_std = np.nanstd(ctrl, axis=0)
        ctrl_mean = np.nan_to_num(ctrl_mean, nan=0.0, posinf=0.0, neginf=0.0)
        ctrl_std = np.nan_to_num(ctrl_std, nan=0.0, posinf=0.0, neginf=0.0)
        eps = 1e-8
        cv = ctrl_std / (np.abs(ctrl_mean) + eps)

        # --- LOEUF per gene from gene_constraint knowledge ---
        loeuf = np.full(n_genes, np.nan, dtype=float)
        gc = ctx.knowledge("gene_constraint")
        if gc is not None:
            cols = gc.get("columns", [])
            genes_tbl = gc.get("genes", {})
            if "oe_lof_upper" in cols:
                idx = cols.index("oe_lof_upper")
                for j, g in enumerate(ctx.genes):
                    vals = genes_tbl.get(g)
                    if vals is None:
                        continue
                    if idx < len(vals):
                        v = vals[idx]
                        if v is not None:
                            try:
                                fv = float(v)
                                if np.isfinite(fv):
                                    loeuf[j] = fv
                            except (TypeError, ValueError):
                                pass

        # Handle missing LOEUF with median of available values.
        finite_mask = np.isfinite(loeuf)
        if finite_mask.any():
            med = float(np.median(loeuf[finite_mask]))
        else:
            med = 1.0
        loeuf = np.where(finite_mask, loeuf, med)
        # Clamp to [0, 1] range for a stable (1 - LOEUF) factor.
        loeuf = np.clip(loeuf, 0.0, 1.0)
        essentiality = 1.0 - loeuf

        # --- per-perturbation target-level scalar ---
        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if len(tgt_idx) == 0:
                continue
            tgt_idx = np.asarray(tgt_idx, dtype=int)
            tgt_idx = tgt_idx[(tgt_idx >= 0) & (tgt_idx < n_genes)]
            if tgt_idx.size == 0:
                continue
            # Average CV and essentiality over targeted genes.
            cv_t = float(np.mean(cv[tgt_idx]))
            ess_t = float(np.mean(essentiality[tgt_idx]))
            val = cv_t * ess_t
            if not np.isfinite(val):
                val = 0.0
            out[i, :, 0] = val

        return out
