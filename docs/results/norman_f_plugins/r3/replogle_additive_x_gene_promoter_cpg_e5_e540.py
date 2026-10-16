import numpy as np
from genemila.features.api import Feature, register

@register
class ReplogleAdditiveXGenePromoterCpG(Feature):
    name = "replogle_additive_x_gene_promoter_cpg_e5_e540"
    version = 1
    description = "Product of sign-corrected Replogle additive response and gene g's cpg_oe_promoter."
    rationale = ("Promoter CpG content modulates CRISPRa efficiency; interacting the "
                 "sign-corrected Replogle additive response with gene g's promoter CpG "
                 "captures how additive activation response scales with CpG content.")
    inputs = ["knowledge", "replogle_additive_response_signed_e104"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        # gene g's cpg_oe_promoter, aligned to ctx.genes
        cpg = np.zeros(n, dtype=float)
        ann = ctx.knowledge("gene_annotation")
        genes_map = None
        if isinstance(ann, dict):
            genes_map = ann.get("genes")
        if isinstance(genes_map, dict):
            cols = None
            if isinstance(ann.get("columns"), list):
                cols = ann["columns"]
            idx = None
            if cols is not None and "cpg_oe_promoter" in cols:
                idx = cols.index("cpg_oe_promoter")
            for j, g in enumerate(ctx.genes):
                v = genes_map.get(g)
                if v is None:
                    continue
                if idx is not None:
                    try:
                        val = v[idx]
                    except Exception:
                        val = None
                else:
                    val = None
                if val is None and isinstance(v, dict):
                    val = v.get("cpg_oe_promoter")
                if val is None:
                    continue
                try:
                    fv = float(val)
                except Exception:
                    continue
                if np.isfinite(fv):
                    cpg[j] = fv

        # sign-corrected Replogle additive response feature
        add = ctx.feature("replogle_additive_response_signed_e104", perts, params)
        add = np.asarray(add, dtype=float)
        if add.ndim == 3:
            add = add[:, :, 0]
        elif add.ndim == 1:
            add = add[:, None]
        # add shape (len(perts), n_genes)

        out = np.zeros((len(perts), n, 1), dtype=float)
        for i in range(len(perts)):
            row = add[i]
            out[i, :, 0] = row * cpg
        return out
