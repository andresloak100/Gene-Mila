import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGcPromoterTimesAdditive(Feature):
    name = "target_gc_promoter_times_additive_e482"
    version = 1
    description = "Mean gc_promoter of p's target genes, multiplied by additive_response."
    rationale = ("CRISPRa targets promoters with dCas9-VP64; GC-rich promoters are more "
                 "accessible, so the effect of the additive response should scale with "
                 "the target promoters' GC content.")
    inputs = ["control_cells", "knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))

        annotation = ctx.knowledge("gene_annotation")
        gc_map = {}
        if annotation is not None:
            genes = annotation.get("genes", {})
            cols = annotation.get("columns", [])
            try:
                gc_idx = cols.index("gc_promoter")
            except ValueError:
                gc_idx = None
            if gc_idx is not None:
                for sym, vals in genes.items():
                    if vals is None:
                        continue
                    v = vals[gc_idx]
                    if v is None:
                        continue
                    try:
                        gc_map[sym] = float(v)
                    except (TypeError, ValueError):
                        continue

        # additive_response predictions, computed once for all perts
        add = ctx.feature("additive_response", perts)
        add = np.asarray(add, dtype=float)
        if add.ndim == 3:
            add = add[:, :, 0]
        elif add.ndim == 1:
            add = add[:, None]

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            vals = [gc_map[g] for g in tgenes if g in gc_map]
            if len(vals) == 0:
                continue
            mean_gc = float(np.mean(vals))
            out[i, :, 0] = mean_gc * add[i]

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
