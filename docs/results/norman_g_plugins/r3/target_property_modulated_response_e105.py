import numpy as np
from genemila.features.api import Feature, register


@register
class TargetPropertyModulatedResponseE105(Feature):
    name = "target_property_modulated_response_e105"
    version = 1
    description = ("additive_response multiplied by the mean control expression of the "
                   "target gene(s) and by (1 - LOEUF) of the target gene(s).")
    rationale = ("Perturbing a highly expressed or LoF-intolerant gene may have stronger "
                 "downstream effects; modulate the additive baseline by target importance.")
    inputs = ["control_mean", "gene_constraint", "additive_response"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))

        # additive_response feature
        add = ctx.feature("additive_response", perts)
        if add.ndim == 3:
            add = add[:, :, 0]
        add = np.asarray(add, dtype=float)

        # constraint table
        cons = ctx.knowledge("gene_constraint") or {}
        cons_genes = cons.get("genes", {})
        cons_cols = cons.get("columns", [])
        try:
            loeuf_idx = cons_cols.index("oe_lof_upper")
        except ValueError:
            loeuf_idx = None

        control_mean = np.asarray(ctx.control_mean, dtype=float)

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            if not tg:
                continue
            # mean control expression of target genes
            cvals = []
            for g in tg:
                j = ctx.gene_index.get(g)
                if j is not None:
                    cvals.append(control_mean[j])
            cmean = float(np.mean(cvals)) if cvals else 0.0

            # mean (1 - LOEUF) of target genes
            lvals = []
            if loeuf_idx is not None:
                for g in tg:
                    row = cons_genes.get(g)
                    if row is None:
                        continue
                    v = row[loeuf_idx]
                    if v is None:
                        continue
                    try:
                        v = float(v)
                    except (TypeError, ValueError):
                        continue
                    if not np.isfinite(v):
                        continue
                    lvals.append(1.0 - v)
            lmean = float(np.mean(lvals)) if lvals else 0.0

            scale = cmean * lmean
            out[i, :, 0] = add[i] * scale

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
