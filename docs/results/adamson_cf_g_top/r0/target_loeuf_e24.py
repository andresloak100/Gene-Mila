import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoeufE24(Feature):
    name = "target_loeuf_e24"
    version = 1
    description = "LOEUF (oe_lof_upper) of the perturbation's target gene; median-imputed if missing."
    rationale = "LoF-intolerant targets (low LOEUF) are likely essential and drive stronger responses."
    inputs = ["knowledge:gene_constraint", "target_indices"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        # Load constraint table once
        table = None
        if "constraint_table" in ctx.cache:
            table = ctx.cache["constraint_table"]
        else:
            kc = ctx.knowledge("gene_constraint")
            genes_map = {}
            col_idx = None
            if kc is not None:
                cols = kc.get("columns", []) if isinstance(kc, dict) else []
                for j, c in enumerate(cols):
                    if c == "oe_lof_upper":
                        col_idx = j
                        break
                g = kc.get("genes", {}) if isinstance(kc, dict) else {}
                if col_idx is not None and isinstance(g, dict):
                    for sym, vals in g.items():
                        if vals is None:
                            continue
                        try:
                            v = vals[col_idx]
                        except (IndexError, TypeError):
                            continue
                        if v is None:
                            continue
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv):
                            genes_map[sym] = fv
            # median for imputation
            if genes_map:
                med = float(np.median(np.array(list(genes_map.values()), dtype=float)))
            else:
                med = 1.0
            table = (genes_map, med)
            ctx.cache["constraint_table"] = table

        genes_map, med = table

        for i, p in enumerate(perts):
            vals = []
            for sym in ctx.target_genes(p):
                if sym in genes_map:
                    vals.append(genes_map[sym])
            score = float(np.mean(vals)) if vals else med
            if not np.isfinite(score):
                score = med
            out[i, :, 0] = score

        return out
