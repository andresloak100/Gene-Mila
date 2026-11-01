import numpy as np
from genemila.features.api import Feature, register


@register
class GeneOeLofLowerXTargetLoeuf(Feature):
    name = "gene_oe_lof_lower_x_target_loeuf_e166"
    version = 1
    description = ("Product of inverted gene oe_lof_lower and inverted target LOEUF "
                   "(1/(1+oe_lof_lower) * 1/(1+LOEUF)).")
    rationale = ("Combines lower-bound LoF constraint of the response gene with target "
                 "intolerance to capture essential gene co-regulation.")
    inputs = ["gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        gc = ctx.knowledge("gene_constraint")
        genes_vals = gc.get("genes", {}) if isinstance(gc, dict) else {}

        # column indices
        cols = gc.get("columns", []) if isinstance(gc, dict) else []
        try:
            i_lower = cols.index("oe_lof_lower")
        except (ValueError, AttributeError):
            i_lower = None
        try:
            i_loeuf = cols.index("oe_lof_upper")
        except (ValueError, AttributeError):
            i_loeuf = None

        # gene g's inverted oe_lof_lower
        gene_term = np.zeros(n_genes, dtype=float)
        for j, g in enumerate(ctx.genes):
            vals = genes_vals.get(g)
            if not vals or i_lower is None or i_lower >= len(vals):
                continue
            v = vals[i_lower]
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv):
                gene_term[j] = 1.0 / (1.0 + fv)

        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            # target LOEUF term
            target_term = 0.0
            tg = ctx.target_genes(p)
            if tg:
                vals = genes_vals.get(tg[0])
                if vals and i_loeuf is not None and i_loeuf < len(vals):
                    v = vals[i_loeuf]
                    if v is not None:
                        try:
                            fv = float(v)
                            if np.isfinite(fv):
                                target_term = 1.0 / (1.0 + fv)
                        except (TypeError, ValueError):
                            pass
            out[i, :, 0] = gene_term * target_term

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
