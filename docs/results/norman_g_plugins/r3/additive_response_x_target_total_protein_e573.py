import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveResponseXTargetTotalProteinE573(Feature):
    name = "additive_response_x_target_total_protein_e573"
    version = 1
    description = "Product of additive_response and the sum of protein lengths of all target genes of perturbation p."
    rationale = ("Longer proteins may require more resources or have different degradation rates; "
                 "the total protein length of the targeted genes may modulate the additive response scaling.")
    inputs = ["protein_annotation", "target_genes"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))

        # additive_response baseline (leakage-safe via its own implementation)
        add = ctx.feature("additive_response", perts)  # (n_perts, n_genes, 1)
        add = np.asarray(add, dtype=float)[:, :, 0]

        # protein length lookup
        pa = ctx.knowledge("protein_annotation")
        prot_len = {}
        if pa is not None:
            cols = pa.get("columns", [])
            genes = pa.get("genes", {})
            if "protein_length" in cols:
                pl_idx = cols.index("protein_length")
                for g, vals in genes.items():
                    if vals is None:
                        continue
                    v = vals[pl_idx]
                    if v is not None:
                        try:
                            prot_len[g] = float(v)
                        except (TypeError, ValueError):
                            pass

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            total = 0.0
            for g in tgenes:
                total += prot_len.get(g, 0.0)
            out[i, :, 0] = add[i] * total

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
