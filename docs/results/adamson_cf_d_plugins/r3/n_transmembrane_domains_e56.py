import numpy as np
from genemila.features.api import Feature, register

@register
class NTransmembraneDomainsE56(Feature):
    name = "n_transmembrane_domains_e56"
    version = 1
    description = "Number of transmembrane segments for gene g's protein (n_transmembrane column)."
    rationale = ("Membrane proteins may have attenuated transcriptional response due to "
                 "post-translational regulation / slower turnover.")
    inputs = ["protein_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = ctx.n_genes
        vec = np.zeros(n, dtype=float)

        pa = ctx.knowledge("protein_annotation")
        if pa is not None:
            genes_tbl = pa.get("genes", {}) or {}
            cols = pa.get("columns", []) or []
            try:
                idx = list(cols).index("n_transmembrane")
            except ValueError:
                idx = None
            if idx is not None:
                for i, g in enumerate(ctx.genes):
                    vals = genes_tbl.get(g)
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
                        vec[i] = fv

        out = np.empty((len(perts), n, 1), dtype=float)
        out[:, :, 0] = vec[np.newaxis, :]
        return out
