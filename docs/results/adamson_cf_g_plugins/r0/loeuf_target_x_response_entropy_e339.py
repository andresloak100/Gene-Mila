import numpy as np
from genemila.features.api import Feature, FeatureContext, register


@register
class LoeufTargetXResponseEntropyE339(Feature):
    name = "loeuf_target_x_response_entropy_e339"
    version = 1
    description = "Product of (1 - LOEUF_target) and response_entropy_e89 for each (p,g)."
    rationale = (
        "Perturbing LoF-intolerant (essential) genes may amplify responses in genes "
        "that are highly variable across training perturbations; the product captures "
        "this synergy between target essentiality and gene-level response entropy."
    )
    inputs = ["knowledge:gene_constraint", "feature:response_entropy_e89"]
    params = {}
    dim = 1

    def compute(self, ctx: FeatureContext, perts: list[str], params: dict) -> np.ndarray:
        n = ctx.n_genes

        # Response entropy per gene (shape (n_genes,) or (len(perts), n_genes, 1))
        ent = ctx.feature("response_entropy_e89", perts, params=None)
        ent = np.asarray(ent, dtype=float)
        if ent.ndim == 3:
            ent = ent[:, :, 0]
        if ent.ndim == 1:
            ent = np.broadcast_to(ent[None, :], (len(perts), n))
        ent = np.nan_to_num(ent, nan=0.0, posinf=0.0, neginf=0.0)

        # LOEUF lookup from gene_constraint knowledge
        loeuf = np.full(n, np.nan, dtype=float)
        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            cols = kc.get("columns", [])
            if "oe_lof_upper" in cols:
                idx = cols.index("oe_lof_upper")
                genes_map = kc.get("genes", {}) or {}
                for gi, g in enumerate(ctx.genes):
                    vals = genes_map.get(g)
                    if vals is None:
                        continue
                    v = vals[idx] if idx < len(vals) else None
                    if v is not None:
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv):
                            loeuf[gi] = fv

        out = np.zeros((len(perts), n, 1), dtype=float)
        for i, p in enumerate(perts):
            # Target LOEUF: average over measured targets (usually one)
            t_idx = ctx.target_indices(p)
            if t_idx:
                vals = loeuf[np.asarray(t_idx, dtype=int)]
                vals = vals[np.isfinite(vals)]
                if vals.size > 0:
                    t_loeuf = float(vals.mean())
                else:
                    t_loeuf = np.nan
            else:
                t_loeuf = np.nan

            if not np.isfinite(t_loeuf):
                # No constraint info: fall back to neutral essentiality weight
                essentiality = 0.0
            else:
                essentiality = 1.0 - t_loeuf

            out[i, :, 0] = essentiality * ent[i]

        return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
