import numpy as np
from genemila.features.api import Feature, register

@register
class AdditiveResponseXTargetProteinLength(Feature):
    name = "additive_response_x_target_protein_lengt_e442"
    version = 1
    description = "Product of additive_response and the mean protein length of the perturbation's target genes."
    rationale = "Protein length of the target may modulate the magnitude of CRISPRa-induced expression changes."
    inputs = ["protein_annotation", "target_genes", "feature"]
    params = {"pair_aggregation": "mean"}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        n_perts = len(perts)

        # additive_response baseline
        add = ctx.feature("additive_response", perts).reshape(n_perts, n_genes)

        # protein lengths per gene
        pa = ctx.knowledge("protein_annotation")
        lengths = np.full(n_genes, np.nan, dtype=np.float64)
        if pa is not None and "genes" in pa and "columns" in pa:
            cols = pa["columns"]
            try:
                li = cols.index("protein_length")
            except ValueError:
                li = 0
            gmap = pa["genes"]
            for g, col in ctx.gene_index.items():
                vals = gmap.get(g)
                if vals is not None and li < len(vals) and vals[li] is not None:
                    try:
                        v = float(vals[li])
                        if np.isfinite(v):
                            lengths[col] = v
                    except (TypeError, ValueError):
                        pass

        # fallback for missing lengths: mean of available
        finite = np.isfinite(lengths)
        fill = float(lengths[finite].mean()) if finite.any() else 0.0
        lengths = np.where(finite, lengths, fill)

        agg = params.get("pair_aggregation", "mean")
        out = np.zeros((n_perts, n_genes, 1), dtype=np.float64)

        for i, p in enumerate(perts):
            tgt = ctx.target_indices(p)
            if len(tgt) == 0:
                tl = 0.0
            else:
                tl_vals = lengths[tgt]
                if agg == "max":
                    tl = float(tl_vals.max())
                elif agg == "sum":
                    tl = float(tl_vals.sum())
                else:
                    tl = float(tl_vals.mean())
            out[i, :, 0] = add[i] * tl

        out = np.where(np.isfinite(out), out, 0.0)
        return out
