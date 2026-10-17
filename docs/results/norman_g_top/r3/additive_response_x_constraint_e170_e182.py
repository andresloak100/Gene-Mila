import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveResponseXConstraintE170E182(Feature):
    name = "additive_response_x_constraint_e170_e182"
    version = 1
    description = ("Product of additive_response (sum over p's target genes of "
                   "their single-gene responses) and the mean LoF-intolerance "
                   "score of p's target genes.")
    rationale = ("Constraint may modulate how strongly a target's activation "
                 "propagates; interacting constraint with the additive baseline "
                 "captures a distinct aspect from is_target-specific constraint.")
    inputs = ["train_delta", "target_genes", "knowledge"]
    params = {"constraint_metric": "loeuf"}
    dim = 1

    def _constraint_scores(self, ctx, metric):
        key = ("constraint_scores", metric)
        if key in ctx.cache:
            return ctx.cache[key]
        scores = np.zeros(ctx.n_genes, dtype=float)
        kdata = ctx.knowledge("gene_constraint")
        if kdata is not None:
            genes = kdata.get("genes", {}) or {}
            cols = list(kdata.get("columns", []) or [])
            if metric == "loeuf":
                col = "oe_lof_upper"
            elif metric == "pli":
                col = "pLI"
            else:
                col = metric
            if col in cols:
                ci = cols.index(col)
                for g, vals in genes.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None or vals is None:
                        continue
                    try:
                        v = vals[ci]
                    except Exception:
                        continue
                    if v is None:
                        continue
                    try:
                        v = float(v)
                    except Exception:
                        continue
                    if not np.isfinite(v):
                        continue
                    if col == "oe_lof_upper":
                        s = 1.0 - v
                    else:
                        s = v
                    scores[gi] = s
        ctx.cache[key] = scores
        return scores

    def _single_response_map(self, ctx, exclude):
        # Build a map gene -> single-gene response vector from training data,
        # excluding the perturbation `exclude` to avoid label leakage.
        key = ("single_response_map", exclude)
        if key in ctx.cache:
            return ctx.cache[key]
        try:
            ids, d = ctx.train_delta(exclude=exclude)
        except Exception:
            ids, d = [], np.zeros((0, ctx.n_genes))
        single_map = {}
        for pid, row in zip(ids, d):
            if pid in ctx.gene_index:
                gi = ctx.gene_index[pid]
                if gi not in single_map:
                    single_map[gi] = row.astype(float)
        ctx.cache[key] = single_map
        return single_map

    def compute(self, ctx, perts, params):
        metric = params.get("constraint_metric", "loeuf")
        scores = self._constraint_scores(ctx, metric)
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            single_map = self._single_response_map(ctx, exclude=p)
            tg = ctx.target_genes(p)
            tgt_idx = [ctx.gene_index[g] for g in tg if g in ctx.gene_index]
            if not tgt_idx:
                continue
            add = np.zeros(ctx.n_genes, dtype=float)
            for gi in tgt_idx:
                if gi in single_map:
                    add += single_map[gi]
            cvals = scores[tgt_idx]
            cmean = float(np.mean(cvals)) if len(cvals) else 0.0
            out[i, :, 0] = add * cmean
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
