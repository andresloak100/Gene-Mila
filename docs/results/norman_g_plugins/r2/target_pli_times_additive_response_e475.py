import numpy as np
from genemila.features.api import Feature, register


@register
class TargetPliTimesAdditiveResponse(Feature):
    name = "target_pli_times_additive_response_e475"
    version = 1
    description = "Mean pLI (LoF intolerance) of p's target genes, multiplied by additive_response."
    rationale = ("Conserved/LoF-intolerant targets may drive more robust regulatory responses; "
                 "interacting constraint with the additive baseline captures this.")
    inputs = ["control_cells", "train_delta", "knowledge"]
    params = {}
    dim = 1

    def _pli_map(self, ctx):
        cache = ctx.cache
        key = "_e475_pli_map"
        if key in cache:
            return cache[key]
        m = {}
        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            cols = kc.get("columns", [])
            genes = kc.get("genes", {}) or {}
            pli_idx = None
            oe_idx = None
            for j, c in enumerate(cols):
                cl = str(c).lower()
                if cl == "pli" or cl == "p_li" or "pli" in cl:
                    pli_idx = j
                if "oe_lof_upper" in cl or "loeuf" in cl:
                    oe_idx = j
            for g, vals in genes.items():
                v = None
                if pli_idx is not None and pli_idx < len(vals) and vals[pli_idx] is not None:
                    try:
                        v = float(vals[pli_idx])
                    except (TypeError, ValueError):
                        v = None
                if v is None and oe_idx is not None and oe_idx < len(vals) and vals[oe_idx] is not None:
                    try:
                        v = float(vals[oe_idx])
                    except (TypeError, ValueError):
                        v = None
                if v is not None and np.isfinite(v):
                    m[g] = v
        cache[key] = m
        return m

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1))
        pli = self._pli_map(ctx)
        # additive baseline: sum of training mean delta over target genes
        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            base = d.mean(axis=0)  # (n_genes,)
            tg = ctx.target_genes(p)
            add = np.zeros(n)
            if tg:
                idx = [ctx.gene_index[g] for g in tg if g in ctx.gene_index]
                if idx:
                    add = base[idx].sum(axis=0)
            vals = [pli[g] for g in tg if g in pli]
            if vals:
                mval = float(np.mean(vals))
            else:
                mval = 0.0
            out[i, :, 0] = mval * add
        out[~np.isfinite(out)] = 0.0
        return out
