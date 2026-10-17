import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoeufXCoexpression(Feature):
    name = "target_loeuf_x_coexpression_e264"
    version = 1
    description = ("Product of the target gene's LOEUF (or pLI) constraint score and the "
                   "Pearson correlation between the target gene and gene g across control cells.")
    rationale = ("Loss-of-function intolerant targets may produce stronger downstream effects, "
                 "but only for genes co-expressed with the target; the product captures this "
                 "constraint-weighted co-expression interaction.")
    inputs = ["control_cells", "gene_corr", "gene_constraint"]
    params = {"constraint_metric": "oe_lof_upper", "default_value": 1.0, "clip": 3.0}
    dim = 1

    def compute(self, ctx, perts, params):
        metric = params.get("constraint_metric", "oe_lof_upper")
        default_value = float(params.get("default_value", 1.0))
        clip = float(params.get("clip", 3.0))

        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # Load constraint table once and map to gene columns.
        constraint_vals = np.full(n_genes, np.nan, dtype=float)
        table = ctx.knowledge("gene_constraint")
        if table is not None:
            cols = table.get("columns", [])
            if metric in cols:
                idx = cols.index(metric)
                genes_dict = table.get("genes", {})
                for g, vals in genes_dict.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None:
                        continue
                    try:
                        v = vals[idx]
                    except (IndexError, TypeError):
                        v = None
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        constraint_vals[gi] = fv

        corr = ctx.gene_corr
        if corr is None:
            corr = np.eye(n_genes, dtype=float)

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            # Use first target column (single-gene targets in this dataset).
            t = tgt_idx[0]
            loeuf = constraint_vals[t]
            if not np.isfinite(loeuf):
                loeuf = default_value
            if clip is not None and clip > 0:
                loeuf = float(np.clip(loeuf, -clip, clip))
            row = corr[t, :].astype(float, copy=True)
            row = np.nan_to_num(row, nan=0.0, posinf=0.0, neginf=0.0)
            out[i, :, 0] = loeuf * row

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
