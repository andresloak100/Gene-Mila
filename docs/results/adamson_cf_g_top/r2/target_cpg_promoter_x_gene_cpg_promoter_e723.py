import numpy as np
from genemila.features.api import Feature, register


@register
class TargetCpgPromoterXGeneCpgPromoterE723(Feature):
    name = "target_cpg_promoter_x_gene_cpg_promoter_e723"
    version = 1
    description = "Product of target gene's cpg_oe_promoter and gene g's cpg_oe_promoter."
    rationale = ("Perturbing a target gene with high promoter CpG density may cause larger "
                 "expression changes in genes with similarly high promoter CpG density, since "
                 "shared chromatin context can mediate co-regulation.")
    inputs = ["knowledge:gene_annotation", "target_genes"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        ann = ctx.knowledge("gene_annotation")
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # Locate the cpg_oe_promoter column index.
        col_idx = None
        if ann is not None:
            columns = ann.get("columns", [])
            try:
                col_idx = columns.index("cpg_oe_promoter")
            except ValueError:
                col_idx = None

        genes_map = ann.get("genes", {}) if ann is not None else {}

        # Build per-gene cpg vector (NaN -> 0).
        gene_cpg = np.zeros(n_genes, dtype=float)
        if col_idx is not None:
            for j, g in enumerate(ctx.genes):
                vals = genes_map.get(g)
                if vals is not None and col_idx < len(vals):
                    v = vals[col_idx]
                    if v is not None:
                        try:
                            fv = float(v)
                            if np.isfinite(fv):
                                gene_cpg[j] = fv
                        except (TypeError, ValueError):
                            pass

        for i, p in enumerate(perts):
            target_cpg = 0.0
            tgenes = ctx.target_genes(p)
            if tgenes:
                acc = []
                for tg in tgenes:
                    vals = genes_map.get(tg)
                    if vals is not None and col_idx is not None and col_idx < len(vals):
                        v = vals[col_idx]
                        if v is not None:
                            try:
                                fv = float(v)
                                if np.isfinite(fv):
                                    acc.append(fv)
                            except (TypeError, ValueError):
                                pass
                if acc:
                    target_cpg = float(np.mean(acc))
            out[i, :, 0] = target_cpg * gene_cpg

        return out
