import numpy as np
from genemila.features.api import Feature, register


@register
class LoeufProductTargetGene(Feature):
    name = "loeuf_product_target_gene_e217"
    version = 1
    description = "Product (1 - LOEUF_target) * (1 - LOEUF_gene) using gnomAD LoF constraint."
    rationale = (
        "Genes under strong LoF constraint (low LOEUF) may be more sensitive to "
        "perturbation; the product of constraint-derived weights for the target "
        "and the responding gene captures a target-modulated sensitivity."
    )
    inputs = ["knowledge", "target_indices"]
    params = {"default": None}
    dim = 1

    def _loeuf_vector(self, ctx):
        cache = ctx.cache
        key = "_loeuf_product_e217_loeuf"
        if key in cache:
            return cache[key]

        loeuf = np.full(ctx.n_genes, np.nan, dtype=float)
        kd = ctx.knowledge("gene_constraint")
        if kd and isinstance(kd, dict):
            genes = kd.get("genes", {})
            columns = kd.get("columns", [])
            try:
                idx = list(columns).index("oe_lof_upper")
            except (ValueError, TypeError):
                idx = None
            if idx is not None and isinstance(genes, dict):
                for g, vals in genes.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None:
                        continue
                    if vals is None:
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

        cache[key] = loeuf
        return loeuf

    def compute(self, ctx, perts, params):
        loeuf = self._loeuf_vector(ctx)
        n = ctx.n_genes

        # Weight per gene: (1 - LOEUF); NaN -> 0 (unknown constraint => no contribution).
        w_gene = np.where(np.isfinite(loeuf), 1.0 - loeuf, 0.0)
        w_gene = np.clip(w_gene, 0.0, None)

        out = np.zeros((len(perts), n, 1), dtype=float)

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if tgt_idx:
                w_t = w_gene[np.asarray(tgt_idx, dtype=int)]
                # Aggregate target weight (mean over targeted genes; typically one).
                w_target = float(np.mean(w_t)) if w_t.size else 0.0
            else:
                w_target = 0.0
            out[i, :, 0] = w_target * w_gene

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
