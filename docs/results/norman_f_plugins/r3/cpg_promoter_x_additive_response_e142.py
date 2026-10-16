import numpy as np
from genemila.features.api import Feature, register


@register
class CpgPromoterXAdditiveResponse(Feature):
    name = "cpg_promoter_x_additive_response_e142"
    version = 1
    description = "Product of cpg_oe_promoter for gene g and additive_response for p."
    rationale = ("CRISPRa efficiency depends on promoter methylation status; the CpG "
                 "observed/expected ratio of a gene's promoter may modulate how strongly "
                 "the additive activation response is expressed.")
    inputs = ["gene_annotation", "additive_response"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        genes = ctx.genes

        # --- CpG observed/expected ratio of the promoter, per gene ---
        cpg = np.zeros(n_genes, dtype=np.float64)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            gdict = ann.get("genes", {}) if isinstance(ann, dict) else {}
            cols = ann.get("columns", []) if isinstance(ann, dict) else []
            idx = None
            for j, c in enumerate(cols):
                if c == "cpg_oe_promoter":
                    idx = j
                    break
            if idx is not None:
                for g in genes:
                    vals = gdict.get(g)
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
                        cpg[ctx.gene_index[g]] = fv

        # --- additive_response feature, shape (n_perts, n_genes, 1) ---
        add = ctx.feature("additive_response", perts)
        add = np.asarray(add, dtype=np.float64)
        if add.ndim == 2:
            add = add[:, :, None]
        base = add[:, :, 0]  # (n_perts, n_genes)

        out = np.zeros((len(perts), n_genes, 1), dtype=np.float64)
        out[:, :, 0] = base * cpg[None, :]
        out[~np.isfinite(out)] = 0.0
        return out
