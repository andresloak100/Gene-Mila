import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoeufXCoexpressionRankE561(Feature):
    name = "target_loeuf_x_coexpression_rank_e561"
    version = 1
    description = (
        "Product of target LOEUF (oe_lof_upper) and the rank of Pearson "
        "correlation between target and gene g across control cells."
    )
    rationale = (
        "Essential targets (low LOEUF) may have coordinated expression programs; "
        "coexpression rank captures functional coupling, and multiplying by LOEUF "
        "amplifies effects for essential targets."
    )
    inputs = ["control_cells", "gene_corr", "knowledge"]
    params = {}
    dim = 1

    def _get_loeuf(self, ctx):
        if "_loeuf_map" in ctx.cache:
            return ctx.cache["_loeuf_map"]
        loeuf = {}
        try:
            kg = ctx.knowledge("gene_constraint")
        except Exception:
            kg = None
        if kg is not None:
            genes = kg.get("genes", {}) or {}
            cols = kg.get("columns", []) or []
            try:
                idx = cols.index("oe_lof_upper")
            except ValueError:
                idx = None
            if idx is not None:
                for g, vals in genes.items():
                    if vals is None:
                        continue
                    try:
                        v = vals[idx]
                    except Exception:
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except Exception:
                        continue
                    if np.isfinite(fv):
                        loeuf[g] = fv
        ctx.cache["_loeuf_map"] = loeuf
        return loeuf

    def _corr_ranks(self, ctx):
        if "_corr_rank" in ctx.cache:
            return ctx.cache["_corr_rank"]
        corr = np.asarray(ctx.gene_corr, dtype=float)
        # rank each row (descending correlation => rank 0 is most correlated)
        # use argsort of -corr; ties broken by order
        order = np.argsort(-corr, axis=1, kind="stable")
        ranks = np.empty_like(order)
        rows = np.arange(corr.shape[0])[:, None]
        ranks[rows, order] = np.arange(corr.shape[1])[None, :]
        ctx.cache["_corr_rank"] = ranks.astype(float)
        return ctx.cache["_corr_rank"]

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        loeuf_map = self._get_loeuf(ctx)
        ranks = self._corr_ranks(ctx)

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            loeuf_val = 0.0
            for tg in tgenes:
                if tg in loeuf_map:
                    loeuf_val = loeuf_map[tg]
                    break
            if loeuf_val == 0.0 or not np.isfinite(loeuf_val):
                # no LOEUF info -> zero row
                continue
            t_idx = ctx.target_indices(p)
            if not t_idx:
                continue
            ti = t_idx[0]
            out[i, :, 0] = loeuf_val * ranks[ti, :]

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
