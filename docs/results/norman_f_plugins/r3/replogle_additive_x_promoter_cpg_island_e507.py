import numpy as np
from genemila.features.api import Feature, register


@register
class ReplogleAdditiveXPromoterCpgIslandE507(Feature):
    name = "replogle_additive_x_promoter_cpg_island_e507"
    version = 1
    description = ("Product of the sign-corrected Replogle additive response and a binary "
                   "indicator that gene g's promoter overlaps a CpG island (high CpG density).")
    rationale = ("CpG islands mark open, permissive chromatin; promoter CpG density may modulate "
                 "how strongly a gene responds to CRISPRa activation, interacting with the "
                 "target-strength signal captured by the Replogle additive response.")
    inputs = ["gene_annotation", "replogle2022_k562"]
    params = {"threshold": 0.6}
    dim = 1

    def compute(self, ctx, perts, params):
        threshold = float(params.get("threshold", 0.6))

        ann = ctx.knowledge("gene_annotation")
        repl = ctx.knowledge("replogle2022_k562")

        n_genes = ctx.n_genes
        genes = ctx.genes

        # --- CpG island indicator per gene g (binary) ---
        cpg_indicator = np.zeros(n_genes, dtype=np.float64)
        if ann is not None:
            ann_genes = ann.get("genes", {}) if isinstance(ann, dict) else {}
            columns = ann.get("columns", []) if isinstance(ann, dict) else []
            try:
                cpg_col = columns.index("cpg_oe_promoter")
            except (ValueError, AttributeError):
                cpg_col = None
            if cpg_col is not None:
                for gi, g in enumerate(genes):
                    vals = ann_genes.get(g)
                    if vals is None:
                        continue
                    try:
                        v = vals[cpg_col]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv) and fv > threshold:
                        cpg_indicator[gi] = 1.0

        # --- sign-corrected Replogle deltas per gene (vector over genes) ---
        repl_vec = np.zeros(n_genes, dtype=np.float64)
        sign = -1.0
        if repl is not None and isinstance(repl, dict):
            try:
                sign = float(repl.get("sign", -1.0))
            except (TypeError, ValueError):
                sign = -1.0
            repl_genes = repl.get("genes", None)
            perts_map = repl.get("perts", {}) or {}
            if repl_genes is not None:
                # map bundle gene -> replogle column
                repl_index = {}
                for ci, rg in enumerate(repl_genes):
                    repl_index[rg] = ci
                for gi, g in enumerate(genes):
                    entry = perts_map.get(g)
                    if entry is None:
                        continue
                    delta = None
                    if isinstance(entry, dict):
                        delta = entry.get("delta", None)
                    if delta is None:
                        continue
                    try:
                        d = np.asarray(delta, dtype=np.float64)
                    except (TypeError, ValueError):
                        continue
                    ci = repl_index.get(g, None)
                    if ci is None:
                        continue
                    if ci < d.shape[0]:
                        val = d[ci]
                        if np.isfinite(val):
                            repl_vec[gi] = sign * val

        # --- per-perturbation additive Replogle response over targets ---
        n_perts = len(perts)
        out = np.zeros((n_perts, n_genes, 1), dtype=np.float64)

        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if not t_idx:
                continue
            add = 0.0
            for ti in t_idx:
                if 0 <= ti < n_genes:
                    add += repl_vec[ti]
            out[i, :, 0] = add * cpg_indicator

        out[~np.isfinite(out)] = 0.0
        return out
