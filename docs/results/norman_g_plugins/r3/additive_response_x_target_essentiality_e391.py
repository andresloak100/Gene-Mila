import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveResponseXTargetEssentialityE391(Feature):
    name = "additive_response_x_target_essentiality_e391"
    version = 1
    description = "Product of additive_response and the mean essentiality score (pLI or 1-LOEUF) of the perturbation's targets."
    rationale = "Additive responses may be stronger when targets are essential (high pLI / low LOEUF); modulating the additive baseline by target essentiality captures this interaction."
    inputs = ["gene_constraint", "train_delta"]
    params = {"essentiality_metric": "pLI"}
    dim = 1

    def _gene_essentiality(self, ctx, metric):
        """Return (n_genes,) normalized essentiality score per gene, 0 where unknown."""
        cache = ctx.cache
        key = ("_e391_ess", metric)
        if key in cache:
            return cache[key]

        score = np.zeros(ctx.n_genes, dtype=float)
        gc = ctx.knowledge("gene_constraint")
        if gc is not None:
            genes = gc.get("genes", {})
            columns = gc.get("columns", [])
            # find column indices
            try:
                idx_pli = columns.index("pLI")
            except ValueError:
                idx_pli = None
            try:
                idx_loeuf = columns.index("oe_lof_upper")
            except ValueError:
                idx_loeuf = None

            use_pli = (metric == "pLI") and (idx_pli is not None)
            use_loeuf = (metric in ("LOEUF", "1-LOEUF", "loeuf")) and (idx_loeuf is not None)
            if not use_pli and not use_loeuf:
                # fallback: prefer pLI, else LOEUF
                if idx_pli is not None:
                    use_pli = True
                elif idx_loeuf is not None:
                    use_loeuf = True

            for g, col in ctx.gene_index.items():
                vals = genes.get(g)
                if vals is None:
                    continue
                if use_pli:
                    v = vals[idx_pli]
                    if v is None:
                        continue
                    v = float(v)
                    if not np.isfinite(v):
                        continue
                    # pLI in [0,1], use directly
                    score[col] = v
                elif use_loeuf:
                    v = vals[idx_loeuf]
                    if v is None:
                        continue
                    v = float(v)
                    if not np.isfinite(v):
                        continue
                    # 1 - LOEUF, clipped to [0,1]-ish
                    s = 1.0 - v
                    if s < 0.0:
                        s = 0.0
                    score[col] = s

        cache[key] = score
        return score

    def _additive_response(self, ctx, p):
        """Sum over p's target genes of their mean training delta (leave p out)."""
        cache = ctx.cache
        key = ("_e391_add", p)
        if key in cache:
            return cache[key]

        tgt = ctx.target_indices(p)
        if not tgt:
            out = np.zeros(ctx.n_genes, dtype=float)
            cache[key] = out
            return out

        _, d = ctx.train_delta(exclude=p)
        mean_delta = d.mean(axis=0)  # (n_genes,)
        out = np.zeros(ctx.n_genes, dtype=float)
        for g in tgt:
            out += mean_delta[g]
        cache[key] = out
        return out

    def compute(self, ctx, perts, params):
        metric = params.get("essentiality_metric", "pLI")
        ess = self._gene_essentiality(ctx, metric)
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            tgt = ctx.target_indices(p)
            if tgt:
                mean_ess = float(np.mean(ess[tgt]))
            else:
                mean_ess = 0.0
            add = self._additive_response(ctx, p)
            out[i, :, 0] = add * mean_ess

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
