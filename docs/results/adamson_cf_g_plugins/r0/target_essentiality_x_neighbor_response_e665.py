import numpy as np
from genemila.features.api import Feature, register

@register
class TargetEssentialityXNeighborResponseE665(Feature):
    name = "target_essentiality_x_neighbor_response_e665"
    version = 1
    description = ("For each (p,g), (1 - LOEUF of perturbation target) * "
                   "target_ppi_neighbor_mean_response_e611_e605.")
    rationale = ("Essential targets may have stronger downstream effects; interacting "
                 "essentiality with neighbor response captures a nonlinear effect that "
                 "the additive linear model may miss.")
    inputs = ["gene_constraint", "feature"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = len(perts)
        ng = ctx.n_genes
        out = np.zeros((n, ng, 1), dtype=float)

        # Fetch the base neighbor-response feature (already defined elsewhere).
        base = ctx.feature(
            "target_ppi_neighbor_mean_response_e611_e605", perts, params=None
        )
        if base is None:
            return out
        base = np.asarray(base, dtype=float)
        if base.ndim == 2:
            base = base[:, :, None]
        if base.shape[0] != n:
            # Fall back to zeros if shape mismatched.
            return out

        # Load LOEUF values from gene_constraint knowledge.
        loeuf = np.full(ng, np.nan, dtype=float)
        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            cols = kc.get("columns", []) or []
            try:
                loeuf_idx = cols.index("oe_lof_upper")
            except ValueError:
                loeuf_idx = None
            genes_map = kc.get("genes", {}) or {}
            if loeuf_idx is not None:
                for gi, g in enumerate(ctx.genes):
                    vals = genes_map.get(g)
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

        # Precompute per-gene essentiality factor (1 - LOEUF), nan-safe.
        ess_gene = np.where(np.isfinite(loeuf), 1.0 - loeuf, 0.0)
        # Clip to reasonable range to avoid extreme values.
        ess_gene = np.clip(ess_gene, 0.0, 2.0)

        # For each perturbation, compute target essentiality factor.
        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                # No target measured: use zero factor (row stays zero).
                continue
            # Average essentiality across target genes (usually one).
            fac = float(np.mean([ess_gene[j] for j in tgt_idx]))
            if not np.isfinite(fac):
                fac = 0.0
            out[i, :, 0] = fac * base[i, :, 0]

        # Ensure finite values.
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
