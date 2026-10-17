import numpy as np
from genemila.features.api import Feature, register


@register
class TargetEssentialityE223(Feature):
    name = "target_essentiality_e223"
    version = 1
    description = ("Combined essentiality score of the perturbation's target gene, from "
                   "gnomAD LoF constraint: pLI if available, else 1 - LOEUF (scaled).")
    rationale = ("Perturbing essential (LoF-intolerant) genes tends to produce larger, more "
                 "widespread expression changes; the target's essentiality modulates the "
                 "magnitude of its downstream response.")
    inputs = ["knowledge", "target_genes"]
    params = {}
    dim = 1

    def _load_constraint(self, ctx):
        cached = ctx.cache.get("_e223_constraint")
        if cached is not None:
            return cached

        raw = ctx.knowledge("gene_constraint")
        score = {}
        if raw is not None:
            cols = raw.get("columns", [])
            genes = raw.get("genes", {}) or {}
            # locate pLI and LOEUF columns case-insensitively
            pli_idx = None
            loeuf_idx = None
            for j, c in enumerate(cols):
                cl = str(c).lower()
                if pli_idx is None and ("pli" == cl or "p_li" == cl or cl == "pli"):
                    pli_idx = j
                if loeuf_idx is None and ("oe_lof_upper" in cl or "loeuf" in cl):
                    loeuf_idx = j
            # fallback: search by substring
            if pli_idx is None:
                for j, c in enumerate(cols):
                    if "pli" in str(c).lower():
                        pli_idx = j
                        break
            for g, vals in genes.items():
                pli = None
                loeuf = None
                if isinstance(vals, (list, tuple)):
                    if pli_idx is not None and pli_idx < len(vals):
                        v = vals[pli_idx]
                        if v is not None:
                            try:
                                pli = float(v)
                            except (TypeError, ValueError):
                                pli = None
                    if loeuf_idx is not None and loeuf_idx < len(vals):
                        v = vals[loeuf_idx]
                        if v is not None:
                            try:
                                loeuf = float(v)
                            except (TypeError, ValueError):
                                loeuf = None
                if pli is not None:
                    score[g] = pli
                elif loeuf is not None:
                    score[g] = 1.0 - loeuf
        ctx.cache["_e223_constraint"] = score
        return score

    def compute(self, ctx, perts, params):
        score_map = self._load_constraint(ctx)
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        # collect per-perturbation target essentiality values
        vals = np.full(len(perts), np.nan, dtype=float)
        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            if not tg:
                continue
            # average over targets that have a score
            s = [score_map[g] for g in tg if g in score_map]
            if s:
                vals[i] = float(np.mean(s))

        finite = np.isfinite(vals)
        if finite.any():
            fill = float(np.median(vals[finite]))
        else:
            fill = 0.0
        vals = np.where(finite, vals, fill)

        # clip to [0,1] for stability
        vals = np.clip(vals, 0.0, 1.0)
        out[:, :, 0] = vals[:, None]
        return out
