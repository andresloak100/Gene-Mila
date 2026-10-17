import numpy as np
from genemila.features.api import Feature, register


@register
class MeanResponseXGeneLoeuf(Feature):
    name = "mean_response_x_gene_loeuf_e274"
    version = 1
    description = "Interaction: leave-one-out mean_response of gene g times gene g's LOEUF (median-filled)."
    rationale = "Essentiality (low LOEUF) may modulate how strongly a gene responds to perturbations, so the generic response program should be scaled by gene constraint."
    inputs = ["train_delta", "gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        gene_index = ctx.gene_index

        # Build per-gene LOEUF vector, median-filled for missing/unmatched.
        loeuf = np.full(n_genes, np.nan, dtype=float)
        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            cols = kc.get("columns", [])
            try:
                col_i = cols.index("oe_lof_upper")
            except ValueError:
                col_i = None
            genes_map = kc.get("genes", {}) or {}
            if col_i is not None:
                for g, vals in genes_map.items():
                    gi = gene_index.get(g)
                    if gi is None or vals is None:
                        continue
                    try:
                        v = vals[col_i]
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

        finite = np.isfinite(loeuf)
        if finite.any():
            med = float(np.median(loeuf[finite]))
        else:
            med = 1.0
        loeuf[~finite] = med

        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            mr = d.mean(axis=0)
            out[i, :, 0] = mr * loeuf

        out[~np.isfinite(out)] = 0.0
        return out
