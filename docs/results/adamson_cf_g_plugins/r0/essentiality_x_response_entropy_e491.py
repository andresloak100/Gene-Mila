import numpy as np
from genemila.features.api import Feature, register


@register
class EssentialityXResponseEntropyE491(Feature):
    name = "essentiality_x_response_entropy_e491"
    version = 1
    description = "Interaction between target essentiality (1 - LOEUF) and response entropy of gene g."
    rationale = ("Essential targets are network hubs; their perturbation causes widespread changes. "
                 "Multiplying target essentiality by per-gene response entropy captures where "
                 "essential perturbations produce the most variable responses.")
    inputs = ["knowledge", "feature"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = len(perts)
        G = ctx.n_genes

        # Response entropy feature (per gene, leave-one-out internally handled by that feature)
        try:
            ent = ctx.feature("response_entropy_e89", perts, params=None)
            ent = np.asarray(ent, dtype=float)
            if ent.ndim == 3:
                ent = ent[:, :, 0]
            elif ent.ndim == 1:
                ent = np.tile(ent[None, :], (n, 1))
            elif ent.ndim == 2 and ent.shape[0] != n:
                ent = np.tile(ent.reshape(1, -1), (n, 1))
        except Exception:
            ent = np.zeros((n, G), dtype=float)

        ent = np.where(np.isfinite(ent), ent, 0.0)

        # LOEUF lookup from gene_constraint knowledge
        loeuf = {}
        try:
            kc = ctx.knowledge("gene_constraint")
            if kc is not None:
                cols = kc.get("columns", [])
                genes = kc.get("genes", {})
                if "oe_lof_upper" in cols:
                    idx = cols.index("oe_lof_upper")
                    for g, vals in genes.items():
                        try:
                            v = vals[idx]
                        except Exception:
                            continue
                        if v is not None:
                            try:
                                fv = float(v)
                                if np.isfinite(fv):
                                    loeuf[g] = fv
                            except Exception:
                                pass
        except Exception:
            loeuf = {}

        out = np.zeros((n, G, 1), dtype=float)
        for i, p in enumerate(perts):
            ess = 0.0
            for tg in ctx.target_genes(p):
                if tg in loeuf:
                    ess = 1.0 - loeuf[tg]
                    break
            if not np.isfinite(ess):
                ess = 0.0
            ess = float(np.clip(ess, 0.0, 1.0))
            out[i, :, 0] = ess * ent[i]

        out = np.where(np.isfinite(out), out, 0.0)
        return out
