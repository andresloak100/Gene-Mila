import numpy as np
from genemila.features.api import Feature, register

@register
class LoeufTargetXGeneEntropyE592(Feature):
    name = "loeuf_target_x_gene_entropy_exxx_e592"
    version = 1
    description = "For each (p,g): (1 - LOEUF of target) multiplied by per-gene response entropy."
    rationale = ("Essential targets (low LOEUF) may trigger widespread coordinated responses; "
                 "coupling target essentiality with gene-level response entropy captures this.")
    inputs = ["control_cells", "knowledge", "feature"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        G = ctx.n_genes

        # Response entropy feature (leave-one-out per perturbation internally)
        ent = ctx.feature("response_entropy_e89", perts, params=None)
        ent = np.asarray(ent, dtype=float)
        if ent.ndim == 3:
            ent2 = ent[:, :, 0]
        elif ent.ndim == 2:
            ent2 = ent
        else:
            ent2 = np.zeros((n_perts, G))
        ent2 = np.where(np.isfinite(ent2), ent2, 0.0)

        # LOEUF per gene from gene_constraint knowledge
        loeuf = np.full(G, np.nan, dtype=float)
        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            cols = kc.get("columns", [])
            genes_map = kc.get("genes", {})
            try:
                li = cols.index("oe_lof_upper")
            except ValueError:
                li = None
            if li is not None:
                for gi, g in enumerate(ctx.genes):
                    vals = genes_map.get(g)
                    if vals is None:
                        continue
                    if li < len(vals):
                        v = vals[li]
                        if v is not None:
                            try:
                                fv = float(v)
                                if np.isfinite(fv):
                                    loeuf[gi] = fv
                            except (TypeError, ValueError):
                                pass

        # Target LOEUF per perturbation; fall back to median of observed LOEUF
        finite_vals = loeuf[np.isfinite(loeuf)]
        if finite_vals.size > 0:
            default_loeuf = float(np.median(finite_vals))
        else:
            default_loeuf = 1.0

        out = np.zeros((n_perts, G, 1), dtype=float)
        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            tl = np.nan
            for ti in tgt_idx:
                if 0 <= ti < G and np.isfinite(loeuf[ti]):
                    tl = loeuf[ti]
                    break
            if not np.isfinite(tl):
                tl = default_loeuf
            ess = 1.0 - tl
            if not np.isfinite(ess):
                ess = 0.0
            out[i, :, 0] = ess * ent2[i]

        out = np.where(np.isfinite(out), out, 0.0)
        return out
