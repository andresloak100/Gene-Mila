import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLoeufTimesIsTargetV2E149(Feature):
    name = "target_loeuf_times_is_target_v2_e149"
    version = 1
    description = ("For perturbation p and gene g, if g is a target of p, use the LOEUF "
                   "of g; otherwise 0.")
    rationale = ("LOEUF captures loss-of-function intolerance; when a gene is directly "
                 "targeted, its intolerance may modulate the magnitude of the response. "
                 "This masks LOEUF by target membership so the model can learn a "
                 "target-specific intolerance effect.")
    inputs = ["control_cells", "knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        # Load LOEUF per gene from gene_constraint knowledge.
        loeuf = np.full(n_genes, np.nan, dtype=float)
        kc = ctx.knowledge("gene_constraint")
        if kc is not None:
            try:
                cols = list(kc.get("columns", []))
                genes_map = kc.get("genes", {}) or {}
                if "oe_lof_upper" in cols:
                    j = cols.index("oe_lof_upper")
                    for g, vals in genes_map.items():
                        gi = ctx.gene_index.get(g)
                        if gi is None:
                            continue
                        try:
                            v = vals[j]
                        except (IndexError, TypeError):
                            continue
                        if v is None:
                            continue
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv):
                            loeuf[gi] = fv
            except Exception:
                pass

        # Replace NaN with 0 (unknown LOEUF -> no contribution).
        loeuf_filled = np.where(np.isfinite(loeuf), loeuf, 0.0)

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            idx = np.asarray(tgt_idx, dtype=int)
            # is_target == 1 for target genes: value = LOEUF of g, else 0.
            out[i, idx, 0] = loeuf_filled[idx]

        return out
