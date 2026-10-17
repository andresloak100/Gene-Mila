import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoeufXGeneControlExpression(Feature):
    name = "target_loeuf_x_gene_control_expression_e523"
    version = 1
    description = "Product of target gene's LOEUF (oe_lof_upper) and gene g's control mean expression."
    rationale = (
        "Perturbing essential (LoF-intolerant) targets may have broader effects on highly "
        "expressed genes, capturing an essentiality-by-expression interaction."
    )
    inputs = ["control_mean", "target_indices", "knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # control mean expression per gene
        ctrl_mean = np.asarray(ctx.control_mean, dtype=float)
        ctrl_mean = np.where(np.isfinite(ctrl_mean), ctrl_mean, 0.0)

        # load LOEUF (oe_lof_upper) from gene_constraint knowledge
        loeuf_by_gene = {}
        knowledge = ctx.knowledge("gene_constraint")
        if knowledge is not None:
            cols = knowledge.get("columns", [])
            try:
                loeuf_idx = cols.index("oe_lof_upper")
            except ValueError:
                loeuf_idx = None
            genes_map = knowledge.get("genes", {})
            if loeuf_idx is not None:
                for sym, vals in genes_map.items():
                    if vals is None:
                        continue
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
                        loeuf_by_gene[sym] = fv

        # default LOEUF for unknown targets: use median of known values (neutral fill)
        if loeuf_by_gene:
            default_loeuf = float(np.median(list(loeuf_by_gene.values())))
        else:
            default_loeuf = 0.0

        for i, p in enumerate(perts):
            target_genes = ctx.target_genes(p)
            loeuf_vals = [loeuf_by_gene.get(tg, default_loeuf) for tg in target_genes]
            if loeuf_vals:
                target_loeuf = float(np.mean(loeuf_vals))
            else:
                target_loeuf = default_loeuf

            row = target_loeuf * ctrl_mean
            out[i, :, 0] = row

        out = np.where(np.isfinite(out), out, 0.0)
        return out
