import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoeufE24(Feature):
    name = "target_loeuf_e24"
    version = 1
    description = "LOEUF (oe_lof_upper) of the target gene of each perturbation; median-imputed when missing."
    rationale = ("Genes intolerant to loss-of-function are more central to cellular fitness, "
                 "so perturbing them triggers broader transcriptional responses (negative coefficient).")
    inputs = ["gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        kc = ctx.knowledge("gene_constraint")
        genes_tbl = {}
        if isinstance(kc, dict):
            genes_tbl = kc.get("genes", {}) or {}

        # column index of oe_lof_upper
        col_idx = None
        if isinstance(kc, dict):
            cols = kc.get("columns", [])
            if isinstance(cols, (list, tuple)) and "oe_lof_upper" in cols:
                col_idx = list(cols).index("oe_lof_upper")

        # collect all LOEUF values (across the whole table) for median imputation
        all_vals = []
        for sym, vals in genes_tbl.items():
            v = None
            if isinstance(vals, dict):
                v = vals.get("oe_lof_upper")
            elif isinstance(vals, (list, tuple)) and col_idx is not None and col_idx < len(vals):
                v = vals[col_idx]
            if v is not None:
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv):
                    all_vals.append(fv)

        if all_vals:
            fill = float(np.median(np.asarray(all_vals, dtype=float)))
        else:
            fill = 0.0

        def loeuf_of(sym):
            vals = genes_tbl.get(sym)
            if vals is None:
                return fill
            v = None
            if isinstance(vals, dict):
                v = vals.get("oe_lof_upper")
            elif isinstance(vals, (list, tuple)) and col_idx is not None and col_idx < len(vals):
                v = vals[col_idx]
            if v is None:
                return fill
            try:
                fv = float(v)
            except (TypeError, ValueError):
                return fill
            return fv if np.isfinite(fv) else fill

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            if not tg:
                val = fill
            else:
                # use first target gene's LOEUF
                val = loeuf_of(tg[0])
            out[i, :, 0] = val

        return out
