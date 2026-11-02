import numpy as np
from genemila.features.api import Feature, register

@register
class MisZGeeE131E143(Feature):
    name = "mis_z_gene_e131_e143"
    version = 1
    description = "Per-gene z-scored missense constraint (mis_z) from gnomAD gene_constraint."
    rationale = "Missense constraint reflects functional importance; genes under stronger constraint may show larger expression changes when perturbed."
    inputs = ["knowledge:gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        raw = np.zeros(n_genes, dtype=float)

        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            genes_tbl = kc.get("genes", {}) or {}
            columns = kc.get("columns", []) or []
            try:
                idx = columns.index("mis_z")
            except ValueError:
                idx = None
            if idx is not None:
                for j, g in enumerate(ctx.genes):
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
                        raw[j] = fv

        # z-score with safe handling
        mu = float(np.mean(raw))
        sd = float(np.std(raw))
        if sd > 1e-12 and np.isfinite(sd):
            z = (raw - mu) / sd
        else:
            z = np.zeros_like(raw)

        # broadcast to (n_perts, n_genes, 1)
        out = np.empty((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = z[None, :]
        # ensure finite
        out = np.where(np.isfinite(out), out, 0.0)
        return out
