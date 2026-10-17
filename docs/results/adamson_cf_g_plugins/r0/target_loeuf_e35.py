import numpy as np
from genemila.features.api import Feature, register

@register
class TargetLOEUF(Feature):
    name = "target_loeuf_e35"
    version = 1
    description = "LOEUF (LoF constraint) value of the perturbation target gene, broadcast across genes."
    rationale = "Perturbing LoF-intolerant (low LOEUF) genes may cause larger transcriptional responses."
    inputs = ["control_cells", "knowledge:gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        n_perts = len(perts)
        out = np.zeros((n_perts, n_genes, 1))

        # Load LOEUF values once
        loeuf = {}
        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            cols = kc.get("columns", [])
            try:
                idx = cols.index("oe_lof_upper")
            except ValueError:
                idx = None
            genes = kc.get("genes", {})
            if idx is not None:
                for sym, vals in genes.items():
                    if vals is None:
                        continue
                    v = vals[idx]
                    if v is not None:
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv):
                            loeuf[sym] = fv

        # Impute median for missing
        if len(loeuf) > 0:
            fill = float(np.median(list(loeuf.values())))
        else:
            fill = 0.0

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            if len(tg) == 0:
                val = fill
            else:
                vals = [loeuf.get(t, fill) for t in tg]
                val = float(np.mean(vals))
            out[i, :, 0] = val

        return out
