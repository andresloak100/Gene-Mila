import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoeufXResponseEntropy(Feature):
    name = "target_loeuf_x_response_entropy_e543_e555"
    version = 1
    description = ("For each (p,g): (1 - LOEUF_target) * response_entropy_e89 for gene g, "
                   "standardized across genes.")
    rationale = ("Essential targets (low LOEUF) may trigger broad, variable transcriptional "
                 "responses; the product with per-gene response entropy captures this synergy.")
    inputs = ["control_cells", "knowledge", "feature"]
    params = {}
    dim = 1

    def _get_loeuf(self, ctx):
        cache = ctx.cache
        key = "loeuf_map_e543_e555"
        if key in cache:
            return cache[key]
        loeuf = {}
        kn = ctx.knowledge("gene_constraint")
        if kn is not None:
            cols = kn.get("columns", [])
            genes = kn.get("genes", {})
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
        cache[key] = loeuf
        return loeuf

    def compute(self, ctx, perts, params):
        n = len(perts)
        n_genes = ctx.n_genes
        out = np.zeros((n, n_genes, 1), dtype=float)

        loeuf_map = self._get_loeuf(ctx)

        # response_entropy feature (per (p,g)); shape (n, n_genes, dim)
        ent = ctx.feature("response_entropy_e89", perts, None)
        ent = np.asarray(ent, dtype=float)
        if ent.ndim == 3:
            ent2 = ent[:, :, 0]
        elif ent.ndim == 2:
            ent2 = ent
        else:
            ent2 = np.full((n, n_genes), float(ent))

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            loeuf_val = None
            for g in tg:
                if g in loeuf_map:
                    loeuf_val = loeuf_map[g]
                    break
            if loeuf_val is None:
                # fall back to a neutral essentiality (median-ish); use 1.0 -> factor 0
                factor = 0.0
            else:
                factor = 1.0 - loeuf_val
            row = factor * ent2[i, :]
            out[i, :, 0] = row

        # Standardize each row across genes (z-score); guard against zero variance
        mu = out.mean(axis=1, keepdims=True)
        sd = out.std(axis=1, keepdims=True)
        sd = np.where(sd > 1e-12, sd, 1.0)
        out = (out - mu) / sd

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
