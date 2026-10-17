import numpy as np
from genemila.features.api import Feature, register


@register
class PairTargetConstraintProduct(Feature):
    name = "pair_target_constraint_product_e476"
    version = 1
    description = "Product of normalized LoF-intolerance scores (1 - LOEUF) of a pair's two target genes; 0 for singles."
    rationale = "Multiplicative interaction of constraint scores may capture nonlinear synergistic constraint effects for pairs."
    inputs = ["knowledge", "target_genes"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        if "gene_constraint" not in ctx.cache:
            k = ctx.knowledge("gene_constraint")
            score = {}
            if k is not None:
                cols = k.get("columns", [])
                genes = k.get("genes", {})
                try:
                    idx = cols.index("oe_lof_upper")
                except ValueError:
                    idx = None
                if idx is not None:
                    for g, vals in genes.items():
                        if vals is None:
                            continue
                        try:
                            v = vals[idx]
                        except Exception:
                            continue
                        if v is None:
                            continue
                        try:
                            v = float(v)
                        except Exception:
                            continue
                        if not np.isfinite(v):
                            continue
                        # Low LOEUF = LoF-intolerant => high constraint score.
                        score[g] = 1.0 - v
            ctx.cache["gene_constraint"] = score
        score = ctx.cache["gene_constraint"]

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            if len(tg) != 2:
                continue
            s0 = score.get(tg[0])
            s1 = score.get(tg[1])
            if s0 is None or s1 is None:
                continue
            out[i, :, 0] = s0 * s1
        return out
