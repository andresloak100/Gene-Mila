import numpy as np
from genemila.features.api import Feature, register


@register
class TargetConstraintE59(Feature):
    name = "target_constraint_e59"
    version = 1
    description = "Average LOEUF of the perturbation's target gene(s), broadcast to all genes."
    rationale = ("Constrained genes (low LOEUF) are functionally important; perturbing them may "
                 "produce larger or more specific responses. Averaging over a pair's targets gives "
                 "an order-independent score.")
    inputs = ["gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        table = ctx.knowledge("gene_constraint")
        if not table or "genes" not in table:
            return out

        cols = list(table.get("columns", []))
        if "oe_lof_upper" not in cols:
            return out
        loeuf_col = cols.index("oe_lof_upper")
        genes = table["genes"]

        # Collect finite LOEUF values for a median fallback.
        vals = []
        for g, row in genes.items():
            if row is None or len(row) <= loeuf_col:
                continue
            v = row[loeuf_col]
            if v is not None:
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv):
                    vals.append(fv)
        median = float(np.median(vals)) if vals else 0.0

        def loeuf_of(g):
            row = genes.get(g)
            if row is None or len(row) <= loeuf_col:
                return median
            v = row[loeuf_col]
            if v is None:
                return median
            try:
                fv = float(v)
            except (TypeError, ValueError):
                return median
            return fv if np.isfinite(fv) else median

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                out[i, :, 0] = median
                continue
            vals_p = [loeuf_of(g) for g in targets]
            out[i, :, 0] = float(np.mean(vals_p))

        return out
