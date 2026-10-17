import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoeufTimesControlMeanE116(Feature):
    name = "target_loeuf_times_control_mean_e116"
    version = 1
    description = "Product of mean LOEUF (or 1 - LOEUF) of target genes and control mean expression of gene g."
    rationale = ("Essential targets (low LOEUF) may have larger effects on highly expressed genes; "
                 "the interaction between target essentiality and baseline expression is captured by "
                 "multiplying target LOEUF-derived score by control_mean of the responding gene.")
    inputs = ["control_mean"]
    params = {"loeuf_transform": "1 - loeuf"}
    dim = 1

    def _load_loeuf(self, ctx):
        cache = ctx.cache
        if "_e116_loeuf" in cache:
            return cache["_e116_loeuf"]
        loeuf = {}
        try:
            ann = ctx.knowledge("gene_constraint")
        except Exception:
            ann = None
        if ann and isinstance(ann, dict):
            genes = ann.get("genes", {})
            cols = ann.get("columns", [])
            if "oe_lof_upper" in cols:
                idx = cols.index("oe_lof_upper")
            else:
                idx = None
            for g, vals in genes.items():
                if vals is None:
                    continue
                try:
                    if idx is not None and idx < len(vals):
                        v = vals[idx]
                    else:
                        # fallback: assume last column is oe_lof_upper
                        v = vals[-1]
                    if v is None:
                        continue
                    fv = float(v)
                    if np.isfinite(fv):
                        loeuf[g] = fv
                except Exception:
                    continue
        cache["_e116_loeuf"] = loeuf
        return loeuf

    def compute(self, ctx, perts, params):
        loeuf_map = self._load_loeuf(ctx)
        transform = params.get("loeuf_transform", "1 - loeuf") if params else "1 - loeuf"

        # Default LOEUF when unknown: neutral value 1.0 for raw loeuf.
        default_loeuf = 1.0

        cm = np.asarray(ctx.control_mean, dtype=float)
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            if not tg:
                continue
            vals = []
            for g in tg:
                v = loeuf_map.get(g, default_loeuf)
                if transform == "1 - loeuf":
                    v = 1.0 - v
                elif transform == "loeuf":
                    pass
                elif transform == "-loeuf":
                    v = -v
                else:
                    v = 1.0 - v
                vals.append(v)
            score = float(np.mean(vals))
            out[i, :, 0] = score * cm

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
