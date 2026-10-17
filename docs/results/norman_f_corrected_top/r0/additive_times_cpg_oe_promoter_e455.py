import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveTimesCpgOePromoterE455(Feature):
    name = "additive_times_cpg_oe_promoter_e455"
    version = 1
    description = "Elementwise product of additive_response and cpg_oe_promoter of gene g."
    rationale = (
        "Promoter CpG observed/expected ratio is associated with gene regulation; "
        "interaction with additive_response may capture response differences."
    )
    inputs = ["gene_annotation", "additive_response"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes

        # --- cpg_oe_promoter per gene (column index 11 per the annotation spec) ---
        cpg = np.zeros(n_genes, dtype=np.float64)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes_ann = ann.get("genes", {})
            columns = ann.get("columns", [])
            # locate cpg_oe_promoter column index
            col_idx = None
            for j, c in enumerate(columns):
                if c == "cpg_oe_promoter":
                    col_idx = j
                    break
            if col_idx is None:
                # fallback: known order -> index 11
                col_idx = 11
            for gi, g in enumerate(ctx.genes):
                vals = genes_ann.get(g)
                if vals is None:
                    continue
                try:
                    v = vals[col_idx]
                except (IndexError, TypeError):
                    continue
                if v is None:
                    continue
                v = float(v)
                if np.isfinite(v):
                    cpg[gi] = v
        # replace any non-finite with 0
        cpg = np.where(np.isfinite(cpg), cpg, 0.0)

        # --- additive_response feature, shape (n_perts, n_genes, dim) ---
        add = ctx.feature("additive_response", perts)
        add = np.asarray(add, dtype=np.float64)
        if add.ndim == 3:
            add2 = add[:, :, 0]
        elif add.ndim == 2:
            add2 = add
        else:
            add2 = np.broadcast_to(add.reshape(-1, 1), (len(perts), n_genes))

        add2 = np.where(np.isfinite(add2), add2, 0.0)

        out = np.zeros((len(perts), n_genes, 1), dtype=np.float64)
        out[:, :, 0] = add2 * cpg[None, :]
        out = np.where(np.isfinite(out), out, 0.0)
        return out
