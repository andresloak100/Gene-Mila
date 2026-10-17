import numpy as np
from genemila.features.api import Feature, register


@register
class PromoterCpGOverlapWithTarget(Feature):
    name = "promoter_cpg_overlap_with_target_e519"
    version = 1
    description = ("Binary: whether gene g's promoter (CpG-island-associated) overlaps, "
                   "within a genomic window, a CpG-island-associated promoter of any target gene of p.")
    rationale = ("Genes whose promoters share CpG-island/active-promoter context are more likely "
                 "to be co-regulated and thus respond when a target gene is perturbed; for pairs "
                 "we use the union of targets.")
    inputs = ["gene_annotation"]
    params = {"window_bp": 2000}
    dim = 1

    def _load(self, ctx):
        if "e519_cache" in ctx.cache:
            return ctx.cache["e519_cache"]
        ann = ctx.knowledge("gene_annotation")
        cache = {"tss": {}, "strand": {}, "cpg": {}}
        if ann is not None:
            loci = ann.get("loci", {}) or {}
            genes_tab = ann.get("genes", {}) or {}
            cols = ann.get("columns", []) or []
            # locate cpg_oe_promoter column
            cpg_idx = None
            for j, c in enumerate(cols):
                if c == "cpg_oe_promoter":
                    cpg_idx = j
                    break
            for g in ctx.genes:
                loc = loci.get(g)
                if loc is not None and len(loc) >= 3:
                    try:
                        tss = float(loc[1])
                    except (TypeError, ValueError):
                        tss = None
                    strand = loc[2]
                    if tss is not None:
                        cache["tss"][g] = tss
                        cache["strand"][g] = strand
                # CpG island promoter indicator from annotation
                val = None
                if cpg_idx is not None:
                    row = genes_tab.get(g)
                    if row is not None and len(row) > cpg_idx:
                        val = row[cpg_idx]
                cache["cpg"][g] = val
        ctx.cache["e519_cache"] = cache
        return cache

    @staticmethod
    def _is_cpg_promoter(val):
        if val is None:
            return False
        try:
            f = float(val)
        except (TypeError, ValueError):
            return False
        if not np.isfinite(f):
            return False
        # cpg_oe_promoter: CpG observed/expected ratio in promoter; >0.6 typical for CpG islands
        return f > 0.6

    def compute(self, ctx, perts, params):
        window = float(params.get("window_bp", 2000))
        cache = self._load(ctx)
        tss = cache["tss"]
        cpg = cache["cpg"]

        # precompute per-gene promoter interval [tss - w, tss + w] and CpG flag
        gene_tss = np.full(ctx.n_genes, np.nan)
        gene_cpg = np.zeros(ctx.n_genes, dtype=bool)
        for idx, g in enumerate(ctx.genes):
            t = tss.get(g)
            if t is not None:
                gene_tss[idx] = t
            gene_cpg[idx] = self._is_cpg_promoter(cpg.get(g))

        out = np.zeros((len(perts), ctx.n_genes, 1))

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            # target promoter intervals restricted to CpG-island promoters
            tgt_tss = []
            for ti in tgt_idx:
                if 0 <= ti < ctx.n_genes and gene_cpg[ti] and np.isfinite(gene_tss[ti]):
                    tgt_tss.append(gene_tss[ti])
            if not tgt_tss:
                continue
            tgt_tss = np.array(tgt_tss, dtype=float)

            # For each gene g with a CpG promoter, check whether its promoter window
            # overlaps any target CpG promoter window.
            valid = gene_cpg & np.isfinite(gene_tss)
            if not np.any(valid):
                continue
            g_tss = gene_tss[valid]
            # overlap if |tss_g - tss_t| <= 2*window (both intervals of half-width window)
            diffs = np.abs(g_tss[:, None] - tgt_tss[None, :])
            overlaps = np.any(diffs <= (2.0 * window), axis=1)
            out[i, valid, 0] = overlaps.astype(float)

        return out
