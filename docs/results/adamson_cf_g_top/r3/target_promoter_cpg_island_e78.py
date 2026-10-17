import numpy as np
from genemila.features.api import Feature, register


@register
class TargetPromoterCpGIslandE78(Feature):
    name = "target_promoter_cpg_island_e78"
    version = 2
    description = (
        "Per-gene score combining target CpG-island status with control-expression "
        "correlation, so downstream genes correlated with CpG-island targets are flagged."
    )
    rationale = (
        "CpG-rich promoters may render targets more CRISPRi-sensitive. Rather than a "
        "row-constant indicator, we weight each downstream gene by its control correlation "
        "to the perturbed target(s), only when the target has a CpG-island promoter. "
        "This produces per-gene, per-perturbation variation."
    )
    inputs = ["knowledge:gene_annotation", "target_indices", "gene_corr"]
    params = {"cpg_oe_threshold": 0.6, "corr_power": 1.0}
    dim = 1

    def _build_lookup(self, ctx, params):
        cache = ctx.cache
        key = "_e78_cpg_lookup_v2"
        if key in cache:
            return cache[key]

        thr = float(params.get("cpg_oe_threshold", 0.6))
        ann = ctx.knowledge("gene_annotation")
        lookup = {}
        if ann is not None and isinstance(ann, dict):
            genes_tbl = ann.get("genes", {}) or {}
            cols = list(ann.get("columns", []) or [])
            idx = None
            for cand in ("cpg_oe_promoter",):
                if cand in cols:
                    idx = cols.index(cand)
                    break
            if idx is not None:
                for sym, vals in genes_tbl.items():
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
                    if not np.isfinite(fv):
                        continue
                    lookup[sym] = 1.0 if fv > thr else 0.0

        cache[key] = lookup
        return lookup

    def compute(self, ctx, perts, params):
        lookup = self._build_lookup(ctx, params)
        power = float(params.get("corr_power", 1.0))
        corr = ctx.gene_corr
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            tgt_idx = [g for g in ctx.target_indices(p) if 0 <= g < ctx.n_genes]
            if not tgt_idx:
                continue
            # only proceed if at least one target has a CpG-island promoter
            has_cpg = False
            for tg in ctx.target_genes(p):
                if lookup.get(tg, 0.0) > 0.0:
                    has_cpg = True
                    break
            if not has_cpg:
                continue

            # per-gene score = mean |corr| to CpG-island targets
            sub = corr[:, tgt_idx]  # (n_genes, n_targets)
            score = np.mean(np.abs(sub), axis=1)
            if power != 1.0:
                score = np.power(np.clip(score, 0.0, 1.0), power)
            out[i, :, 0] = score

        out[~np.isfinite(out)] = 0.0
        return out
