import numpy as np
from genemila.features.api import Feature, register


@register
class ReplogleAdditiveXTargetPromoterCpG(Feature):
    name = "replogle_additive_x_target_promoter_cpg_e528"
    version = 1
    description = "Product of sign-corrected Replogle additive response and mean promoter CpG o/e ratio of p's targets."
    rationale = ("CRISPRa efficiency depends on promoter CpG content; combining the Replogle-derived additive "
                 "response with the target genes' promoter CpG o/e ratio captures a chromatin-dependent "
                 "modulation of activation strength.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        base = ctx.feature("replogle_additive_response_signed_e104", perts)
        base = np.asarray(base, dtype=float)
        if base.ndim == 3:
            base = base[:, :, 0]
        elif base.ndim == 1:
            base = base[:, None]

        ann = ctx.knowledge("gene_annotation")
        cpg = None
        if ann is not None:
            genes = ann.get("genes", {}) if isinstance(ann, dict) else {}
            columns = ann.get("columns", []) if isinstance(ann, dict) else []
            if "cpg_oe_promoter" in columns:
                idx = columns.index("cpg_oe_promoter")
                cpg = {}
                for g, vals in genes.items():
                    if vals is None:
                        continue
                    try:
                        v = vals[idx]
                    except (TypeError, IndexError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        cpg[g] = fv

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            mean_cpg = 0.0
            if cpg is not None and targets:
                vals = [cpg[g] for g in targets if g in cpg]
                if vals:
                    mean_cpg = float(np.mean(vals))
            out[i, :, 0] = base[i] * mean_cpg

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
