import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGeneLoeufProductE537(Feature):
    name = "target_gene_loeuf_product_e537"
    version = 1
    description = (
        "Product of inverse target LOEUF and inverse gene LOEUF (1/LOEUF), "
        "emphasising essentiality of both the perturbed target and each gene."
    )
    rationale = (
        "Essential (LoF-intolerant) targets are network hubs; disrupting them may "
        "disproportionately affect other constrained genes. Using inverse LOEUF "
        "amplifies essentiality signals relative to the raw-value product."
    )
    inputs = ["knowledge", "target_genes"]
    params = {"transform": "inverse"}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # Load gene LOEUF values from gene_constraint prior knowledge.
        gene_loeuf = np.full(n_genes, np.nan, dtype=float)
        kn = ctx.knowledge("gene_constraint")
        if kn is not None:
            cols = kn.get("columns", [])
            try:
                loeuf_col = cols.index("oe_lof_upper")
            except ValueError:
                loeuf_col = None
            genes_map = kn.get("genes", {}) or {}
            if loeuf_col is not None:
                for g, vals in genes_map.items():
                    idx = ctx.gene_index.get(g)
                    if idx is None:
                        continue
                    if vals is None or loeuf_col >= len(vals):
                        continue
                    v = vals[loeuf_col]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        gene_loeuf[idx] = fv

        # Inverse transform with guards against zero / non-positive values.
        with np.errstate(divide="ignore", invalid="ignore"):
            gene_inv = np.where(
                np.isfinite(gene_loeuf) & (gene_loeuf > 0),
                1.0 / gene_loeuf,
                0.0,
            )
        gene_inv = np.where(np.isfinite(gene_inv), gene_inv, 0.0)
        gene_inv = np.clip(gene_inv, 0.0, 1e6)

        transform = params.get("transform", "inverse") if params else "inverse"

        for i, p in enumerate(perts):
            tidx = ctx.target_indices(p)
            if not tidx:
                continue
            tv = [gene_inv[j] for j in tidx if gene_inv[j] > 0]
            if not tv:
                continue
            target_inv = float(np.mean(tv))
            if target_inv <= 0:
                continue
            if transform == "inverse":
                row = target_inv * gene_inv
            else:
                # fallback: raw product using original LOEUF if available
                tv_raw = [gene_loeuf[j] for j in tidx if np.isfinite(gene_loeuf[j])]
                if not tv_raw:
                    continue
                target_raw = float(np.mean(tv_raw))
                row = target_raw * np.where(np.isfinite(gene_loeuf), gene_loeuf, 0.0)
            out[i, :, 0] = row

        out = np.where(np.isfinite(out), out, 0.0)
        return out
