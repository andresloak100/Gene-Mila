import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveResponseXLoeuf(Feature):
    name = "additive_response_x_loeuf_e203"
    version = 1
    description = (
        "Product of the additive response prediction and the mean normalized "
        "LoF-intolerance (1 - LOEUF) of the perturbation's target genes."
    )
    rationale = (
        "LoF-intolerant genes are tightly regulated; activating them may trigger "
        "stronger downstream programs, so the additive response should scale with "
        "target LoF intolerance."
    )
    inputs = ["train_delta", "knowledge:gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        # --- Load gene_constraint prior ---
        kc = ctx.knowledge("gene_constraint")
        loeuf_raw = {}
        if kc is not None:
            genes_tbl = kc.get("genes", {}) or {}
            cols = kc.get("columns", []) or []
            try:
                loeuf_idx = cols.index("oe_lof_upper")
            except ValueError:
                loeuf_idx = None
            if loeuf_idx is not None:
                for sym, vals in genes_tbl.items():
                    if vals is None:
                        continue
                    try:
                        v = vals[loeuf_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        loeuf_raw[sym] = fv

        # --- Normalize LOEUF to [0,1] intolerance score: 1 - loeuf, clipped ---
        # LOEUF typically in [0, ~2+]; clip to [0,1] before inverting.
        # Genes with no LOEUF get a neutral 0.5 intolerance (so product ~ additive).
        def intolerance(sym):
            if sym in loeuf_raw:
                lo = min(max(loeuf_raw[sym], 0.0), 1.0)
                return 1.0 - lo
            return 0.5

        cache = ctx.cache
        if "loeuf_intol" not in cache:
            cache["loeuf_intol"] = {}
        intol_cache = cache["loeuf_intol"]

        def target_intol(p):
            if p in intol_cache:
                return intol_cache[p]
            tgenes = ctx.target_genes(p)
            if not tgenes:
                val = 0.5
            else:
                vals = [intolerance(g) for g in tgenes]
                val = float(np.mean(vals))
            intol_cache[p] = val
            return val

        out = np.zeros((len(perts), ctx.n_genes, 1))
        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            additive = d.mean(axis=0)  # (n_genes,)
            scale = target_intol(p)
            out[i, :, 0] = additive * scale

        # Ensure finite
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
