import numpy as np
from genemila.features.api import Feature, register

@register
class ReplogleAdditiveXPromoterCpgoe(Feature):
    name = "replogle_additive_x_promoter_cpg_oe_e441"
    version = 1
    description = "Product of sign-corrected Replogle additive response and gene g's cpg_oe_promoter from gene_annotation."
    rationale = "Promoter CpG content influences transcriptional regulation; genes with high CpG islands may respond differently to CRISPRa."
    inputs = ["replogle2022_k562", "gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # Load cpg_oe_promoter per gene
        cpg = np.zeros(n_genes, dtype=float)
        ann = ctx.knowledge("gene_annotation") or {}
        genes_map = ann.get("genes", {}) if isinstance(ann, dict) else {}
        cols = ann.get("columns", []) if isinstance(ann, dict) else []
        try:
            idx = cols.index("cpg_oe_promoter")
        except (ValueError, AttributeError):
            idx = None
        if idx is not None:
            for g, gi in ctx.gene_index.items():
                vals = genes_map.get(g)
                if vals is not None and idx < len(vals):
                    v = vals[idx]
                    if v is not None:
                        try:
                            fv = float(v)
                            if np.isfinite(fv):
                                cpg[gi] = fv
                        except (TypeError, ValueError):
                            pass

        # Load Replogle data
        rp = ctx.knowledge("replogle2022_k562") or {}
        sign = rp.get("sign", -1) if isinstance(rp, dict) else -1
        rp_perts = rp.get("perts", {}) if isinstance(rp, dict) else {}
        rp_genes = rp.get("genes", []) if isinstance(rp, dict) else []
        rp_index = {g: i for i, g in enumerate(rp_genes)}

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            add = np.zeros(n_genes, dtype=float)
            for tg in targets:
                entry = rp_perts.get(tg)
                if entry is None:
                    continue
                delta = entry.get("delta") if isinstance(entry, dict) else None
                if delta is None:
                    continue
                for gi, g in enumerate(ctx.genes):
                    ri = rp_index.get(g)
                    if ri is None or ri >= len(delta):
                        continue
                    v = delta[ri]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        add[gi] += sign * fv
            out[i, :, 0] = add * cpg

        # Ensure finite
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
