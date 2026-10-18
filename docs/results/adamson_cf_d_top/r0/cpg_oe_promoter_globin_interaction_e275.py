import numpy as np
from genemila.features.api import Feature, register


@register
class CpgOePromoterGlobinInteraction(Feature):
    name = "cpg_oe_promoter_globin_interaction_e275"
    version = 1
    description = "cpg_oe_promoter of gene g if g is a globin gene, else 0."
    rationale = ("Globin genes with high CpG island promoter overlap may be more "
                 "sensitive to perturbations affecting methylation or chromatin state.")
    inputs = ["gene_annotation"]
    params = {"globin_genes": ["HBZ", "HBG1", "HBG2", "HBA1"]}
    dim = 1

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1))

        globin = params.get("globin_genes", ["HBZ", "HBG1", "HBG2", "HBA1"])
        globin_idx = [ctx.gene_index[g] for g in globin if g in ctx.gene_index]
        if not globin_idx:
            return out

        ann = ctx.knowledge("gene_annotation")
        if ann is None or "genes" not in ann or "columns" not in ann:
            return out

        cols = ann["columns"]
        try:
            col_i = cols.index("cpg_oe_promoter")
        except ValueError:
            return out

        table = ann["genes"]
        vals = np.zeros(n, dtype=float)
        for gi in globin_idx:
            sym = ctx.genes[gi]
            row = table.get(sym)
            if row is None or col_i >= len(row):
                continue
            v = row[col_i]
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv):
                vals[gi] = fv

        out[:, :, 0] = vals[None, :]
        return out
