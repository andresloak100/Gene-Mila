import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLofIntoleranceE191(Feature):
    name = "target_lof_intolerance_e191"
    version = 1
    description = "Mean LOEUF (oe_lof_upper) of the target genes of perturbation p."
    rationale = ("Genes under strong purifying selection (low LOEUF) may have more "
                 "sensitive regulatory networks, so activating them yields larger downstream effects.")
    inputs = ["target_genes", "knowledge:gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))

        kc = ctx.knowledge("gene_constraint")
        loeuf = {}
        if kc is not None:
            genes_tbl = kc.get("genes", {})
            cols = kc.get("columns", [])
            try:
                idx = cols.index("oe_lof_upper")
            except ValueError:
                idx = None
            if idx is not None:
                for g, vals in genes_tbl.items():
                    if vals is None:
                        continue
                    try:
                        v = vals[idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        loeuf[g] = fv

        if len(loeuf) > 0:
            med = float(np.median(np.array(list(loeuf.values()), dtype=float)))
        else:
            med = 1.0

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            if not tg:
                out[i, :, 0] = med
                continue
            vals = [loeuf.get(g, med) for g in tg]
            out[i, :, 0] = float(np.mean(vals))

        out = np.nan_to_num(out, nan=med, posinf=med, neginf=med)
        return out
