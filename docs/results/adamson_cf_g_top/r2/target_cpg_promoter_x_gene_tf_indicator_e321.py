import numpy as np
from genemila.features.api import Feature, register


@register
class TargetCpgPromoterXGeneTfIndicatorE321(Feature):
    name = "target_cpg_promoter_x_gene_tf_indicator_e321"
    version = 1
    description = "Product of target gene's cpg_oe_promoter and an indicator that gene g is a transcription factor."
    rationale = ("CpG-rich promoters mark actively transcribed genes; perturbing such targets may "
                 "preferentially disrupt regulatory complexes, so the effect on transcription-factor "
                 "genes is scaled by the target's promoter CpG density.")
    inputs = ["gene_annotation", "transcription_factors"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        cpg = {}
        if ann is not None:
            cols = ann.get("columns", [])
            genes = ann.get("genes", {})
            if "cpg_oe_promoter" in cols:
                idx = cols.index("cpg_oe_promoter")
                for sym, vals in genes.items():
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
                        cpg[sym] = fv

        tfs = ctx.knowledge("transcription_factors")
        tf_set = set(tfs) if tfs is not None else set()

        tf_indicator = np.zeros(ctx.n_genes, dtype=float)
        for g in tf_set:
            j = ctx.gene_index.get(g)
            if j is not None:
                tf_indicator[j] = 1.0

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            cpg_val = 0.0
            for t in tg:
                if t in cpg:
                    cpg_val = cpg[t]
                    break
            if cpg_val == 0.0 or not np.isfinite(cpg_val):
                continue
            out[i, :, 0] = cpg_val * tf_indicator

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
