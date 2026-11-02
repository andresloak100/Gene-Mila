import numpy as np
from genemila.features.api import Feature, register

@register
class TargetCpGIslandPromoterXGlobinGene(Feature):
    name = "target_cpg_oe_promoter_x_globin_gene_e276"
    version = 1
    description = "Target gene's CpG island promoter overlap, gated to globin genes."
    rationale = "Targets with high CpG island promoter overlap are more likely to be epigenetic regulators, so perturbing them may affect globin gene expression."
    inputs = ["gene_annotation"]
    params = {"globin_genes": ["HBZ", "HBG1", "HBG2", "HBA1"]}
    dim = 1

    def compute(self, ctx, perts, params):
        globin_genes = params.get("globin_genes", ["HBZ", "HBG1", "HBG2", "HBA1"])
        globin_mask = np.zeros(ctx.n_genes, dtype=bool)
        for g in globin_genes:
            idx = ctx.gene_index.get(g)
            if idx is not None:
                globin_mask[idx] = True

        annot = ctx.knowledge("gene_annotation") or {}
        columns = annot.get("columns", [])
        try:
            col_idx = columns.index("cpg_oe_promoter")
        except ValueError:
            col_idx = None
        gene_vals = annot.get("genes", {})

        out = np.zeros((len(perts), ctx.n_genes, 1))
        for i, p in enumerate(perts):
            target_genes = ctx.target_genes(p)
            target_val = 0.0
            if col_idx is not None:
                for tg in target_genes:
                    vals = gene_vals.get(tg)
                    if vals is not None:
                        v = vals[col_idx]
                        if v is not None:
                            try:
                                target_val = float(v)
                            except (TypeError, ValueError):
                                target_val = 0.0
                            break
            if target_val != 0.0:
                out[i, globin_mask, 0] = target_val
        return out
