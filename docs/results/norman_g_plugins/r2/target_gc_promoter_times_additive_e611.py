import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGcPromoterTimesAdditive(Feature):
    name = "target_gc_promoter_times_additive_e611"
    version = 1
    description = "Mean gc_promoter of p's target genes multiplied by additive_response."
    rationale = ("Promoter GC content influences transcriptional regulation and may modulate "
                 "CRISPRa efficiency, so it scales the additive baseline response.")
    inputs = ["gene_annotation", "additive_response"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        ann = ctx.knowledge("gene_annotation")
        gc_map = {}
        if ann is not None and isinstance(ann, dict):
            genes_tbl = ann.get("genes", {}) or {}
            cols = ann.get("columns", []) or []
            gc_idx = None
            for j, c in enumerate(cols):
                if c == "gc_promoter":
                    gc_idx = j
                    break
            if gc_idx is not None:
                for sym, vals in genes_tbl.items():
                    try:
                        v = vals[gc_idx]
                    except Exception:
                        v = None
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except Exception:
                        continue
                    if np.isfinite(fv):
                        gc_map[sym] = fv

        # additive_response feature
        add = ctx.feature("additive_response", perts)
        if add.ndim == 2:
            add = add[:, :, None]

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            vals = [gc_map[g] for g in tgenes if g in gc_map]
            if len(vals) > 0:
                mean_gc = float(np.mean(vals))
            else:
                mean_gc = 0.0
            out[i, :, 0] = mean_gc * add[i, :, 0]

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
