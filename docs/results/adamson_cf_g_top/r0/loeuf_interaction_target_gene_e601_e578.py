import numpy as np
from genemila.features.api import Feature, register


@register
class LoeufInteractionTargetGene(Feature):
    name = "loeuf_interaction_target_gene_e601_e578"
    version = 1
    description = "Product of (1 - LOEUF_target) and (1 - LOEUF_gene) for each (p, g)."
    rationale = (
        "Essential targets (low LOEUF) may trigger broader compensatory responses; "
        "the interaction between target and gene essentiality captures this."
    )
    inputs = ["target_genes", "knowledge"]
    params = {}
    dim = 1

    def _load_loeuf(self, ctx):
        cache_key = "_loeuf_interaction_e601_e578"
        if cache_key in ctx.cache:
            return ctx.cache[cache_key]
        loeuf = np.full(ctx.n_genes, np.nan, dtype=np.float64)
        gc = ctx.knowledge("gene_constraint")
        if gc is not None:
            genes = gc.get("genes", {}) if isinstance(gc, dict) else {}
            cols = gc.get("columns", []) if isinstance(gc, dict) else []
            try:
                idx = list(cols).index("oe_lof_upper")
            except ValueError:
                idx = None
            if idx is not None:
                for g, vals in genes.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None or vals is None:
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
                    if np.isfinite(fv):
                        loeuf[gi] = fv
        finite = loeuf[np.isfinite(loeuf)]
        fill = float(np.median(finite)) if finite.size > 0 else 1.0
        loeuf = np.where(np.isfinite(loeuf), loeuf, fill)
        # essentiality score: (1 - LOEUF), clipped to sane range
        ess = 1.0 - np.clip(loeuf, 0.0, 2.0)
        ctx.cache[cache_key] = ess
        return ess

    def compute(self, ctx, perts, params):
        ess = self._load_loeuf(ctx)  # (n_genes,)
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=np.float64)
        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            # average essentiality across targets (usually one)
            tgt_ess = float(np.mean(ess[tgt_idx]))
            out[i, :, 0] = tgt_ess * ess
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
