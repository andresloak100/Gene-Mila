import numpy as np
from genemila.features.api import Feature, register


@register
class TargetIntronLengthTimesAdditive(Feature):
    name = "target_intron_length_times_additive_e483"
    version = 1
    description = "Mean intron_length_kb of p's target genes, multiplied by additive_response."
    rationale = ("Longer introns may harbor more regulatory elements, so intron length of the "
                 "targeted genes modulates the CRISPRa response magnitude.")
    inputs = ["knowledge", "feature"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        ann = ctx.knowledge("gene_annotation")
        intron_idx = None
        intron_map = {}
        if ann is not None and "columns" in ann:
            try:
                intron_idx = ann["columns"].index("intron_length_kb")
            except (ValueError, AttributeError):
                intron_idx = None
        if ann is not None and intron_idx is not None:
            genes_tbl = ann.get("genes", {}) or {}
            for g, vals in genes_tbl.items():
                if vals is not None and len(vals) > intron_idx:
                    v = vals[intron_idx]
                    if v is not None:
                        try:
                            fv = float(v)
                            if np.isfinite(fv):
                                intron_map[g] = fv
                        except (TypeError, ValueError):
                            pass

        add = ctx.feature("additive_response", perts)
        add = np.asarray(add, dtype=float)
        if add.ndim == 3:
            add2 = add[:, :, 0]
        elif add.ndim == 2:
            add2 = add
        else:
            add2 = add.reshape(len(perts), ctx.n_genes)

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            vals = [intron_map[g] for g in tg if g in intron_map]
            if vals:
                m = float(np.mean(vals))
            else:
                m = 0.0
            out[i, :, 0] = m * add2[i]
        out[~np.isfinite(out)] = 0.0
        return out
