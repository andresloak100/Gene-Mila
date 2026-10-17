import numpy as np
from genemila.features.api import Feature, register


@register
class TargetCpgPromoterE190(Feature):
    name = "target_cpg_promoter_e190"
    version = 1
    description = "Mean cpg_oe_promoter of target genes of perturbation p."
    rationale = ("CRISPRa efficiency depends on promoter accessibility; CpG island overlap "
                 "of the target's promoter reflects its activatability and downstream effect.")
    inputs = ["control_cells", "knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))

        ann = ctx.knowledge("gene_annotation")
        if ann is None:
            return out

        genes_tbl = ann.get("genes", {})
        cols = ann.get("columns", [])
        try:
            cpg_idx = cols.index("cpg_oe_promoter")
        except ValueError:
            return out

        # Build lookup: gene symbol -> cpg_oe_promoter value (float or nan)
        def get_val(g):
            row = genes_tbl.get(g)
            if row is None:
                return np.nan
            try:
                v = row[cpg_idx]
            except (IndexError, TypeError):
                return np.nan
            if v is None:
                return np.nan
            try:
                return float(v)
            except (TypeError, ValueError):
                return np.nan

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue
            vals = [get_val(g) for g in targets]
            vals = [v for v in vals if np.isfinite(v)]
            if vals:
                out[i, :, 0] = float(np.mean(vals))

        return out
