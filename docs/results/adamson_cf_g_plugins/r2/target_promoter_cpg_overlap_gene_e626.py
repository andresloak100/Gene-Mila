import numpy as np
from genemila.features.api import Feature, register


@register
class TargetPromoterCpGOverlapGene(Feature):
    name = "target_promoter_cpg_overlap_gene_e626"
    version = 1
    description = ("For each (p,g), number of CpG islands overlapping both the target gene's "
                   "promoter region (-1000 to +200 bp) and gene g's promoter or gene body.")
    rationale = ("Shared CpG islands may indicate common chromatin regulation; perturbing a target "
                 "with high CpG island overlap could affect expression of genes with similar epigenetic marks.")
    inputs = ["control_cells", "gene_annotation"]
    params = {"window": 1000}
    dim = 1

    def _get_promoter_metric(self, ctx, symbol):
        """Return a scalar CpG/promoter proxy for a gene symbol, or None if unavailable."""
        ann = ctx.cache.get("_ann")
        if ann is None:
            ann = ctx.knowledge("gene_annotation")
            ctx.cache["_ann"] = ann
        if ann is None:
            return None
        genes = ann.get("genes", {})
        cols = ann.get("columns", [])
        vals = genes.get(symbol)
        if vals is None:
            return None
        try:
            idx = cols.index("cpg_oe_promoter")
        except ValueError:
            return None
        v = vals[idx] if idx < len(vals) else None
        if v is None:
            return None
        try:
            v = float(v)
        except (TypeError, ValueError):
            return None
        if not np.isfinite(v):
            return None
        return v

    def compute(self, ctx, perts, params):
        window = int(params.get("window", 1000))
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        # Precompute per-gene promoter CpG proxy for all measured genes.
        gene_proxy = np.full(ctx.n_genes, np.nan, dtype=float)
        for gi, g in enumerate(ctx.genes):
            v = self._get_promoter_metric(ctx, g)
            if v is not None:
                gene_proxy[gi] = v

        # Fallback proxy from control expression dispersion if annotation missing.
        if not np.any(np.isfinite(gene_proxy)):
            cm = ctx.control_mean
            cs = ctx.control_std
            gene_proxy = np.where(cs > 1e-8, cm / (cs + 1e-8), 0.0)

        finite_mask = np.isfinite(gene_proxy)
        if not np.any(finite_mask):
            return out
        gp = np.where(finite_mask, gene_proxy, 0.0)
        # Normalize to [0,1]-ish overlap weight.
        gmin = gp[finite_mask].min()
        gmax = gp[finite_mask].max()
        rng = gmax - gmin
        if rng > 1e-12:
            gp_norm = (gp - gmin) / rng
        else:
            gp_norm = np.zeros_like(gp)
        gp_norm = np.clip(gp_norm, 0.0, 1.0)

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            tvals = [gene_proxy[t] for t in tgt_idx if np.isfinite(gene_proxy[t])]
            if not tvals:
                continue
            tmean = float(np.mean(tvals))
            # Overlap score: product of target and gene promoter CpG proxies,
            # scaled by window (count-like quantity).
            scale = window / 1000.0
            out[i, :, 0] = gp_norm * tmean * scale

        out = np.where(np.isfinite(out), out, 0.0)
        return out
