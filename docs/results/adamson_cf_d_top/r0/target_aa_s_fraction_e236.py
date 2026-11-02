import numpy as np
from genemila.features.api import Feature, register

@register
class TargetAaSFractionE236(Feature):
    name = "target_aa_s_fraction_e236"
    version = 1
    description = "Fraction of serine residues in the protein of the targeted gene p."
    rationale = ("Serine-rich proteins are heavily phosphorylated; perturbing them may "
                 "disrupt signaling cascades and produce larger expression changes.")
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if not ann or "genes" not in ann or "columns" not in ann:
            return out

        cols = ann["columns"]
        try:
            s_idx = cols.index("aa_S")
        except ValueError:
            return out

        genes_tbl = ann["genes"]

        cache = ctx.cache.setdefault("e236_aa_s", {})
        if not cache:
            for sym, vals in genes_tbl.items():
                v = None
                if vals is not None and s_idx < len(vals):
                    v = vals[s_idx]
                cache[sym] = v

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            if not tg:
                continue
            vals = []
            for t in tg:
                v = cache.get(t)
                if v is not None:
                    try:
                        fv = float(v)
                        if np.isfinite(fv):
                            vals.append(fv)
                    except (TypeError, ValueError):
                        pass
            if vals:
                out[i, :, 0] = float(np.mean(vals))

        return out
