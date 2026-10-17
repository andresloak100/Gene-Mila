import numpy as np
from genemila.features.api import Feature, register


@register
class TargetPLITimesAdditiveResponse(Feature):
    name = "target_pli_times_additive_response_e216"
    version = 1
    description = ("Product of the mean pLI (probability of loss-of-function intolerance) "
                   "of p's target genes and additive_response.")
    rationale = ("Essential genes (high pLI) are highly connected in regulatory networks; "
                 "their activation may have broader downstream consequences, so scale the "
                 "additive baseline by the mean target pLI.")
    inputs = ["control_cells", "gene_constraint"]
    params = {"pLI_column": "pLI"}
    dim = 1

    def compute(self, ctx, perts, params):
        col_name = params.get("pLI_column", "pLI")

        # Load pLI per gene from gene_constraint knowledge.
        pLI = np.full(ctx.n_genes, np.nan, dtype=float)
        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            cols = kc.get("columns", [])
            genes_tbl = kc.get("genes", {})
            if col_name in cols:
                j = cols.index(col_name)
                for g, vals in genes_tbl.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None or vals is None:
                        continue
                    v = vals[j]
                    if v is None:
                        continue
                    try:
                        pLI[gi] = float(v)
                    except (TypeError, ValueError):
                        continue

        # Mean pLI per target set (unordered set of targets).
        def mean_pli(p):
            tg = ctx.target_genes(p)
            if not tg:
                return 0.0
            vals = []
            for g in tg:
                gi = ctx.gene_index.get(g)
                if gi is not None and np.isfinite(pLI[gi]):
                    vals.append(pLI[gi])
            if not vals:
                return 0.0
            return float(np.mean(vals))

        # Additive response: sum over targets of each gene's mean training delta.
        _, d_train = ctx.train_delta(exclude=perts[0]) if len(perts) > 0 else (None, None)
        # Per-perturbation additive baseline, computed with leakage-safe train_delta.
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            mean_delta = d.mean(axis=0)  # (n_genes,)
            tg = ctx.target_genes(p)
            add = np.zeros(ctx.n_genes, dtype=float)
            for g in tg:
                gi = ctx.gene_index.get(g)
                if gi is not None:
                    add += mean_delta  # each target contributes the full per-gene baseline
            # "sum over p's target genes of each gene's [mean delta]": per gene g, sum over
            # targets of mean_delta[g] = len(targets) * mean_delta[g]. Use additive_response
            # composition instead for consistency with the existing feature.
            add = np.zeros(ctx.n_genes, dtype=float)
            for g in tg:
                gi = ctx.gene_index.get(g)
                if gi is not None:
                    add += mean_delta
            scale = mean_pli(p)
            out[i, :, 0] = scale * add
        return out
