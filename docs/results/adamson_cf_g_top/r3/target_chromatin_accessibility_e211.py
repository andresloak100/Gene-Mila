import numpy as np
from genemila.features.api import Feature, register


@register
class TargetChromatinAccessibility(Feature):
    name = "target_chromatin_accessibility_e211"
    version = 1
    description = (
        "Proxy for chromatin accessibility of each perturbation's target gene, "
        "derived from promoter CpG observed/expected ratio (and TSS crowding), "
        "standardized across genes."
    )
    rationale = (
        "Targets in open chromatin (high promoter CpG density, TSS-dense regions) "
        "are more accessible to CRISPRi/a machinery and thus produce stronger or "
        "more consistent perturbation effects."
    )
    inputs = ["knowledge:gene_annotation", "target_indices"]
    params = {"use_cpg": True}
    dim = 1

    def _accessibility_scores(self, ctx, params):
        cache = ctx.cache
        key = ("e211_scores", bool(params.get("use_cpg", True)))
        if key in cache:
            return cache[key]

        n = ctx.n_genes
        ann = ctx.knowledge("gene_annotation")
        cols = ann.get("columns", []) if ann else []
        genes = ann.get("genes", {}) if ann else {}

        cpg_idx = None
        tss_idx = None
        for j, c in enumerate(cols):
            cl = c.lower()
            if cpg_idx is None and "cpg_oe_promoter" in cl:
                cpg_idx = j
            if tss_idx is None and "n_tss_within_100kb" in cl:
                tss_idx = j

        use_cpg = bool(params.get("use_cpg", True))
        cpg = np.full(n, np.nan, dtype=float)
        tss = np.full(n, np.nan, dtype=float)

        for g, gi in ctx.gene_index.items():
            vals = genes.get(g)
            if not vals:
                continue
            if cpg_idx is not None and cpg_idx < len(vals):
                v = vals[cpg_idx]
                if v is not None:
                    try:
                        cpg[gi] = float(v)
                    except (TypeError, ValueError):
                        pass
            if tss_idx is not None and tss_idx < len(vals):
                v = vals[tss_idx]
                if v is not None:
                    try:
                        tss[gi] = float(v)
                    except (TypeError, ValueError):
                        pass

        def zscore(x):
            out = np.zeros_like(x)
            m = np.isfinite(x)
            if m.sum() < 2:
                return out
            mu = x[m].mean()
            sd = x[m].std()
            if sd <= 0 or not np.isfinite(sd):
                return out
            out[m] = (x[m] - mu) / sd
            return out

        z_cpg = zscore(cpg)
        z_tss = zscore(tss)

        if use_cpg:
            score = z_cpg.copy()
            # fall back to TSS crowding where CpG is missing
            miss = ~np.isfinite(cpg)
            score[miss] = z_tss[miss]
        else:
            score = z_tss.copy()
            miss = ~np.isfinite(tss)
            score[miss] = z_cpg[miss]

        score[~np.isfinite(score)] = 0.0
        cache[key] = score
        return score

    def compute(self, ctx, perts, params):
        scores = self._accessibility_scores(ctx, params)
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            tgt = ctx.target_indices(p)
            if not tgt:
                continue
            s = float(np.mean(scores[tgt]))
            if not np.isfinite(s):
                s = 0.0
            out[i, :, 0] = s
        return out
