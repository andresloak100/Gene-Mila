import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoeufXGeneControlMeanE320(Feature):
    name = "target_loeuf_x_gene_control_mean_e320"
    version = 1
    description = (
        "Product of target gene's inverted LOEUF (1 - LOEUF, high = essential) "
        "and gene g's control mean expression."
    )
    rationale = (
        "Essential target genes (low LOEUF) likely produce broad downstream effects; "
        "highly expressed genes may be more sensitive to perturbation."
    )
    inputs = ["control_mean", "gene_constraint", "targets"]
    params = {}
    dim = 1

    def _load_loeuf(self, ctx):
        cached = ctx.cache.get("_e320_loeuf")
        if cached is not None:
            return cached
        loeuf = {}
        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            cols = kc.get("columns", [])
            genes = kc.get("genes", {})
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
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        loeuf[g] = fv
        ctx.cache["_e320_loeuf"] = loeuf
        return loeuf

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        n_genes = ctx.n_genes
        out = np.zeros((n_perts, n_genes, 1), dtype=float)

        loeuf_map = self._load_loeuf(ctx)
        control_mean = np.asarray(ctx.control_mean, dtype=float)
        control_mean = np.where(np.isfinite(control_mean), control_mean, 0.0)

        for i, p in enumerate(perts):
            target_genes = ctx.target_genes(p)
            loeuf_vals = []
            for tg in target_genes:
                if tg in loeuf_map:
                    loeuf_vals.append(loeuf_map[tg])
            if loeuf_vals:
                tgt_loeuf = float(np.mean(loeuf_vals))
            else:
                tgt_loeuf = 0.5
            essentiality = 1.0 - tgt_loeuf
            out[i, :, 0] = essentiality * control_mean

        out = np.where(np.isfinite(out), out, 0.0)
        return out
