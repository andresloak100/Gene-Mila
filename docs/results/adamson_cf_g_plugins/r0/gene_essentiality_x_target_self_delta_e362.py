import numpy as np
from genemila.features.api import Feature, register


@register
class GeneEssentialityXTargetSelfDelta(Feature):
    name = "gene_essentiality_x_target_self_delta_e362"
    version = 1
    description = (
        "For each (p,g): (1 - LOEUF_gene) * target_self_delta_e54, where "
        "target_self_delta_e54 is the average self-delta of the perturbation target."
    )
    rationale = (
        "Essential genes may be downstream effectors of target perturbations, so their "
        "response may scale with target knockdown efficiency."
    )
    inputs = ["gene_constraint", "feature"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        n_genes = ctx.n_genes

        # --- LOEUF per gene from gene_constraint ---
        loeuf = np.full(n_genes, np.nan, dtype=float)
        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            columns = kc.get("columns", [])
            try:
                loeuf_idx = columns.index("oe_lof_upper")
            except ValueError:
                loeuf_idx = None
            if loeuf_idx is not None:
                genes_map = kc.get("genes", {}) or {}
                for gi, gname in enumerate(ctx.genes):
                    vals = genes_map.get(gname)
                    if vals is None:
                        continue
                    if loeuf_idx < len(vals):
                        v = vals[loeuf_idx]
                        if v is not None:
                            try:
                                fv = float(v)
                            except (TypeError, ValueError):
                                continue
                            if np.isfinite(fv):
                                loeuf[gi] = fv

        # Missing LOEUF -> treat as non-essential (1 - LOEUF = 0)
        essentiality = np.where(np.isfinite(loeuf), 1.0 - loeuf, 0.0)
        essentiality = np.clip(essentiality, 0.0, None)
        essentiality = np.where(np.isfinite(essentiality), essentiality, 0.0)

        # --- target_self_delta_e54 feature: (n_perts,) per-perturbation scalar ---
        self_delta = ctx.feature(
            "target_self_delta_e54", perts, params=None
        )
        self_delta = np.asarray(self_delta, dtype=float)
        # Reduce to per-perturbation scalar
        if self_delta.ndim == 1:
            sd = self_delta
        else:
            sd = self_delta.reshape(self_delta.shape[0], -1)
            # take mean over gene dim; if it was already constant, this is fine
            sd = np.nanmean(sd, axis=1)
        sd = np.where(np.isfinite(sd), sd, 0.0)

        # --- outer product: (n_perts, n_genes) ---
        out = sd[:, None] * essentiality[None, :]
        out = np.where(np.isfinite(out), out, 0.0)
        return out[:, :, None]
