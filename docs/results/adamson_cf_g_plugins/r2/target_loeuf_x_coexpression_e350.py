import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoeufXCoexpression(Feature):
    name = "target_loeuf_x_coexpression_e350"
    version = 1
    description = (
        "Product of target gene's LOEUF (oe_lof_upper from gene_constraint) and "
        "the Pearson correlation between target and gene g across control cells."
    )
    rationale = (
        "Essential genes (low LOEUF) tend to be network hubs; their perturbation "
        "should propagate more strongly to coexpressed genes. LOEUF gives a "
        "continuous essentiality measure that modulates coexpression propagation."
    )
    inputs = ["control_cells", "gene_corr", "gene_constraint"]
    params = {"impute_missing": "median"}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # ---- Load LOEUF values for all genes ----
        cache = ctx.cache
        key = ("loeuf_values_e350",)
        if key in cache:
            loeuf = cache[key]
        else:
            loeuf = np.full(n_genes, np.nan, dtype=float)
            gc = ctx.knowledge("gene_constraint")
            if gc is not None:
                cols = gc.get("columns", [])
                try:
                    idx = cols.index("oe_lof_upper")
                except ValueError:
                    idx = None
                genes_map = gc.get("genes", {})
                if idx is not None and isinstance(genes_map, dict):
                    for g, vals in genes_map.items():
                        gi = ctx.gene_index.get(g)
                        if gi is None:
                            continue
                        try:
                            v = vals[idx]
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
            cache[key] = loeuf

        # ---- Impute missing LOEUF ----
        impute = params.get("impute_missing", "median")
        loeuf_filled = loeuf.copy()
        finite_mask = np.isfinite(loeuf_filled)
        if finite_mask.any():
            if impute == "median":
                fill = float(np.median(loeuf_filled[finite_mask]))
            elif impute == "mean":
                fill = float(np.mean(loeuf_filled[finite_mask]))
            else:
                fill = float(np.median(loeuf_filled[finite_mask]))
        else:
            fill = 0.0
        loeuf_filled[~finite_mask] = fill

        # ---- Coexpression matrix (cached) ----
        corr_key = ("gene_corr_e350",)
        if corr_key in cache:
            corr = cache[corr_key]
        else:
            corr = ctx.gene_corr
            if corr is None:
                X = np.asarray(ctx.control_cells, dtype=float)
                # center and normalize per gene
                Xc = X - X.mean(axis=0, keepdims=True)
                norms = np.sqrt((Xc * Xc).sum(axis=0, keepdims=True))
                norms[norms == 0] = 1.0
                Xn = Xc / norms
                corr = Xn.T @ Xn
                np.clip(corr, -1.0, 1.0, out=corr)
            cache[corr_key] = corr

        # ---- Per-perturbation computation ----
        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if not t_idx:
                # no measured target -> feature is zero
                continue
            t = int(t_idx[0])
            loeuf_t = loeuf_filled[t]
            coexp_row = corr[t, :]
            vals = loeuf_t * coexp_row
            vals = np.where(np.isfinite(vals), vals, 0.0)
            out[i, :, 0] = vals

        return out
