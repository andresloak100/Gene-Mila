import numpy as np
from genemila.features.api import Feature, register


@register
class TFBSCountPromoter(Feature):
    name = "tfbs_count_promoter_e341"
    version = 1
    description = (
        "Per-gene promoter regulatory complexity proxy: number of predicted TF "
        "binding sites in the promoter region, derived from promoter sequence "
        "features and upstream TSS counts in the gene_annotation knowledge."
    )
    rationale = (
        "Genes with more TF binding sites in their promoters have higher "
        "regulatory complexity and are expected to be more responsive to "
        "perturbations, especially when a TF is targeted. We approximate TFBS "
        "density from promoter GC content, CpG observed/expected ratio, the "
        "number of upstream ATGs, and the number of TSSs within 100 kb, which "
        "co-vary with promoter regulatory element density."
    )
    inputs = ["knowledge"]
    params = {"promoter_window": "[-1000, 200]"}
    dim = 1

    def _build_scores(self, ctx):
        cache = ctx.cache
        key = "tfbs_count_promoter_e341_scores"
        if key in cache:
            return cache[key]

        n = ctx.n_genes
        scores = np.zeros(n, dtype=float)

        ka = ctx.knowledge("gene_annotation")
        if ka is None:
            cache[key] = scores
            return scores

        columns = ka.get("columns", []) or []
        col_index = {c: i for i, c in enumerate(columns)}
        genes = ka.get("genes", {}) or {}

        # Locate the relevant annotation columns; fall back to None if absent.
        def idx(name):
            return col_index.get(name, None)

        i_gc = idx("gc_promoter")
        i_cpg = idx("cpg_oe_promoter")
        i_atg = idx("n_upstream_atg")
        i_tss = idx("n_tss_within_100kb")
        i_span = idx("gene_span_kb")

        raw = np.zeros((n, 5), dtype=float)
        present = np.zeros((n, 5), dtype=bool)

        for g in ctx.genes:
            vals = genes.get(g, None)
            if not isinstance(vals, (list, tuple)):
                continue
            gi = ctx.gene_index.get(g, None)
            if gi is None:
                continue
            row = [i_gc, i_cpg, i_atg, i_tss, i_span]
            for j, ci in enumerate(row):
                if ci is None:
                    continue
                try:
                    v = vals[ci]
                except Exception:
                    continue
                if v is None:
                    continue
                try:
                    fv = float(v)
                except Exception:
                    continue
                if not np.isfinite(fv):
                    continue
                raw[gi, j] = fv
                present[gi, j] = True

        # Z-score each component among genes where it is present and normalize.
        comp = np.zeros_like(raw)
        for j in range(raw.shape[1]):
            mask = present[:, j]
            if mask.sum() < 2:
                continue
            v = raw[mask, j]
            mu = v.mean()
            sd = v.std()
            if sd <= 1e-9:
                continue
            z = (raw[:, j] - mu) / sd
            z[~mask] = 0.0
            comp[:, j] = z

        # Weighted combination: GC and CpG positively, upstream ATGs and TSS
        # counts positively (more regulatory elements / alternative promoters),
        # gene span mildly positive.
        w = np.array([1.0, 1.0, 0.5, 1.0, 0.3], dtype=float)
        combined = comp @ w

        # Convert to a non-negative "count-like" score via softplus.
        scores = np.log1p(np.exp(np.clip(combined, -30.0, 30.0)))

        # Genes with no annotation at all get 0.
        any_present = present.any(axis=1)
        scores[~any_present] = 0.0

        if not np.all(np.isfinite(scores)):
            scores = np.nan_to_num(scores, nan=0.0, posinf=0.0, neginf=0.0)

        cache[key] = scores
        return scores

    def compute(self, ctx, perts, params):
        scores = self._build_scores(ctx)
        n = len(perts)
        out = np.empty((n, ctx.n_genes, 1), dtype=float)
        out[:, :, 0] = scores[None, :]
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
