import numpy as np
from genemila.features.api import Feature, register


@register
class TargetPromoterAccessibility(Feature):
    name = "target_promoter_accessibility_e365"
    version = 1
    description = (
        "Estimated promoter accessibility of the perturbation's target gene, "
        "combining GC content and CpG observed/expected ratio in the promoter "
        "region from gene_annotation. Broadcast to all genes."
    )
    rationale = (
        "Perturbation of genes in open/accessible chromatin regions may produce "
        "more pronounced downstream effects because the locus is actively "
        "regulated; combining GC content and CpG density gives a proxy for "
        "promoter accessibility."
    )
    inputs = ["control_cells", "knowledge"]
    params = {"combine": "mean"}
    dim = 1

    def _load_annotation(self, ctx):
        if "_tpa_ann" in ctx.cache:
            return ctx.cache["_tpa_ann"]
        ann = ctx.knowledge("gene_annotation")
        gc = None
        cpg = None
        gene_index = {}
        if ann is not None:
            cols = ann.get("columns", [])
            genes = ann.get("genes", {})
            try:
                i_gc = cols.index("gc_promoter")
            except ValueError:
                i_gc = None
            try:
                i_cpg = cols.index("cpg_oe_promoter")
            except ValueError:
                i_cpg = None
            if i_gc is not None or i_cpg is not None:
                n = len(genes)
                gc = np.full(n, np.nan)
                cpg = np.full(n, np.nan)
                for j, (sym, vals) in enumerate(genes.items()):
                    gene_index[sym] = j
                    if i_gc is not None and i_gc < len(vals):
                        v = vals[i_gc]
                        if v is not None:
                            try:
                                gc[j] = float(v)
                            except (TypeError, ValueError):
                                pass
                    if i_cpg is not None and i_cpg < len(vals):
                        v = vals[i_cpg]
                        if v is not None:
                            try:
                                cpg[j] = float(v)
                            except (TypeError, ValueError):
                                pass
        result = (gc, cpg, gene_index)
        ctx.cache["_tpa_ann"] = result
        return result

    def _combine(self, gc, cpg, combine):
        # normalize each to [0,1] robustly (min-max over finite values)
        def norm(x):
            out = np.full_like(x, np.nan, dtype=float)
            finite = np.isfinite(x)
            if not np.any(finite):
                return out
            lo = np.nanmin(x[finite])
            hi = np.nanmax(x[finite])
            if hi > lo:
                out[finite] = (x[finite] - lo) / (hi - lo)
            else:
                out[finite] = 0.0
            return out

        gc_n = norm(gc)
        cpg_n = norm(cpg)

        if combine == "gc":
            score = gc_n
        elif combine == "cpg":
            score = cpg_n
        elif combine == "product":
            score = gc_n * cpg_n
        else:  # "mean"
            both = np.isfinite(gc_n) & np.isfinite(cpg_n)
            score = np.full_like(gc_n, np.nan, dtype=float)
            score[both] = 0.5 * (gc_n[both] + cpg_n[both])
            only_gc = np.isfinite(gc_n) & ~np.isfinite(cpg_n)
            score[only_gc] = gc_n[only_gc]
            only_cpg = np.isfinite(cpg_n) & ~np.isfinite(gc_n)
            score[only_cpg] = cpg_n[only_cpg]

        finite = np.isfinite(score)
        if np.any(finite):
            med = np.median(score[finite])
        else:
            med = 0.0
        score[~finite] = med
        return score

    def compute(self, ctx, perts, params):
        combine = params.get("combine", "mean")
        gc, cpg, gene_index = self._load_annotation(ctx)

        n_genes = ctx.n_genes
        # Build per-gene accessibility score over annotation genes, then map to ctx genes
        gene_score = np.zeros(n_genes, dtype=float)
        if gc is not None and cpg is not None and len(gene_index) > 0:
            combined = self._combine(gc, cpg, combine)
            default = float(np.median(combined)) if combined.size else 0.0
            for gi, sym in enumerate(ctx.genes):
                j = gene_index.get(sym)
                if j is not None:
                    gene_score[gi] = combined[j]
                else:
                    gene_score[gi] = default
        # else all zeros (neutral)

        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            targets = ctx.target_indices(p)
            if targets:
                # average over target columns (usually one)
                val = float(np.mean(gene_score[targets]))
            else:
                val = 0.0
            out[i, :, 0] = val
        return out
