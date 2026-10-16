import numpy as np
from genemila.features.api import Feature, register


@register
class TargetMeanCpGOePromoter(Feature):
    name = "target_mean_cpg_oe_promoter_e402_e350"
    version = 1
    description = "Mean of cpg_oe_promoter across p's target genes."
    rationale = ("CpG observed/expected ratio in promoters modulates target gene regulation; "
                 "targets with high CpG O/E may show stronger CRISPRa responses.")
    inputs = ["knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        ann = ctx.knowledge("gene_annotation")
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        if not ann or "genes" not in ann:
            return out

        genes_ann = ann["genes"]
        columns = ann.get("columns", [])
        try:
            col_idx = columns.index("cpg_oe_promoter")
        except ValueError:
            return out

        # Build a lookup for cpg_oe_promoter per gene symbol
        cpg_lookup = {}
        for sym, vals in genes_ann.items():
            if vals is None or col_idx >= len(vals):
                continue
            v = vals[col_idx]
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv):
                cpg_lookup[sym] = fv

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            vals = [cpg_lookup[g] for g in targets if g in cpg_lookup]
            if vals:
                out[i, :, 0] = float(np.mean(vals))
            # else stays 0.0

        return out
