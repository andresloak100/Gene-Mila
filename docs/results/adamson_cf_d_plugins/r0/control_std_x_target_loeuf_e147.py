import numpy as np
from genemila.features.api import Feature, register


@register
class ControlStdXTargetLoeuf(Feature):
    name = "control_std_x_target_loeuf_e147"
    version = 1
    description = "Product of control_std of gene g and the LOEUF of the target gene p."
    rationale = ("Perturbing essential genes (low LOEUF) may cause larger fluctuations "
                 "in highly variable genes.")
    inputs = ["control_std", "gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes

        # control_std vector for all genes
        cstd = np.asarray(ctx.control_std, dtype=float).ravel()
        if cstd.shape[0] != n_genes:
            cstd = np.resize(cstd, n_genes)
        cstd = np.nan_to_num(cstd, nan=0.0, posinf=0.0, neginf=0.0)

        # Load gene_constraint prior knowledge and find LOEUF column
        loeuf_map = {}
        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            columns = kc.get("columns", []) or []
            genes_tbl = kc.get("genes", {}) or {}
            # locate LOEUF column index
            loeuf_idx = None
            for j, c in enumerate(columns):
                if str(c).lower() == "oe_lof_upper":
                    loeuf_idx = j
                    break
            if loeuf_idx is None:
                # fallback: look for any column containing 'loeuf'
                for j, c in enumerate(columns):
                    if "loeuf" in str(c).lower():
                        loeuf_idx = j
                        break
            if loeuf_idx is not None:
                for g, vals in genes_tbl.items():
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
                        loeuf_map[g] = fv

        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            # target LOEUF: use target genes of perturbation p
            tgenes = ctx.target_genes(p)
            loeuf_vals = [loeuf_map[g] for g in tgenes if g in loeuf_map]
            if loeuf_vals:
                target_loeuf = float(np.mean(loeuf_vals))
            else:
                # unknown target constraint -> neutral (no effect)
                target_loeuf = 0.0
            out[i, :, 0] = cstd * target_loeuf

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
