import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoeufXMeanResponse(Feature):
    name = "target_loeuf_x_mean_response_e404"
    version = 1
    description = (
        "Product of (1 - LOEUF of the perturbation target) and the leave-one-out "
        "mean response of gene g across training perturbations."
    )
    rationale = (
        "LoF-intolerant (essential) targets may drive stronger downstream responses; "
        "scaling the generic mean response by target essentiality captures genes that "
        "are especially sensitive to perturbations of essential targets."
    )
    inputs = ["train_delta", "knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        # Load LoF constraint table once and build a LOEUF lookup.
        loeuf = {}
        if "loeuf" not in ctx.cache:
            cons = ctx.knowledge("gene_constraint")
            mapping = {}
            if cons is not None:
                cols = cons.get("columns", [])
                genes_tbl = cons.get("genes", {}) or {}
                if "oe_lof_upper" in cols:
                    j = cols.index("oe_lof_upper")
                    for g, vals in genes_tbl.items():
                        if vals is not None and j < len(vals):
                            v = vals[j]
                            if v is not None:
                                mapping[g] = float(v)
            ctx.cache["loeuf"] = mapping
        loeuf = ctx.cache["loeuf"]

        # Default essentiality factor for targets missing LOEUF.
        default_factor = 0.5

        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            mean_resp = d.mean(axis=0)  # (n_genes,)

            factor = default_factor
            tgenes = ctx.target_genes(p)
            if tgenes:
                vals = [loeuf[g] for g in tgenes if g in loeuf]
                if vals:
                    loeuf_t = float(np.mean(vals))
                    factor = 1.0 - loeuf_t

            out[i, :, 0] = factor * mean_resp

        return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
