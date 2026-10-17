import numpy as np
from genemila.features.api import Feature, register

@register
class EssentialityPathwayInteractionE65(Feature):
    name = "essentiality_pathway_interaction_e65"
    version = 1
    description = "Interaction between target LOEUF (or pLI) and pathway overlap score."
    rationale = "Essential genes (low LOEUF) with many shared pathways may produce larger downstream effects on related genes."
    inputs = ["control_cells", "knowledge"]
    params = {"loeuf_feature": "target_loeuf_e35", "default_loeuf": 1.0}
    dim = 1

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        n_genes = ctx.n_genes
        out = np.zeros((n_perts, n_genes, 1), dtype=float)

        loeuf_feature = params.get("loeuf_feature", "target_loeuf_e35")
        default_loeuf = float(params.get("default_loeuf", 1.0))

        # Pathway overlap feature (dim = n_genes presumably)
        try:
            pathway_arr = ctx.feature("pathway_overlap_score_e13", perts)
        except Exception:
            pathway_arr = None

        # LOEUF feature
        try:
            loeuf_arr = ctx.feature(loeuf_feature, perts)
        except Exception:
            loeuf_arr = None

        # Fallback LOEUF from gene_constraint knowledge
        constraint = ctx.knowledge("gene_constraint")
        loeuf_col = None
        if constraint is not None:
            cols = constraint.get("columns", [])
            for idx, c in enumerate(cols):
                if c == "oe_lof_upper":
                    loeuf_col = idx
                    break

        def get_loeuf_for_pert(i, p):
            if loeuf_arr is not None:
                v = np.asarray(loeuf_arr[i])
                # reduce to scalar if multiple dims
                if v.ndim > 0 and v.size > 0:
                    val = float(np.nanmean(v))
                    if np.isfinite(val):
                        return val
            # fallback: look up target gene in constraint table
            if constraint is not None and loeuf_col is not None:
                tg = ctx.target_genes(p)
                genes_tbl = constraint.get("genes", {})
                vals = []
                for g in tg:
                    entry = genes_tbl.get(g)
                    if entry is not None and entry[loeuf_col] is not None:
                        try:
                            vals.append(float(entry[loeuf_col]))
                        except (TypeError, ValueError):
                            pass
                if vals:
                    return float(np.mean(vals))
            return default_loeuf

        for i, p in enumerate(perts):
            loeuf_val = get_loeuf_for_pert(i, p)
            # essentiality weight: low LOEUF -> high essentiality
            # use inverse-ish transform, bounded
            if not np.isfinite(loeuf_val) or loeuf_val <= 0:
                ess = 0.0
            else:
                ess = 1.0 / (1.0 + loeuf_val)

            if pathway_arr is not None:
                pw = np.asarray(pathway_arr[i], dtype=float)
                if pw.ndim == 2:
                    pw = pw[:, 0]
                pw = np.nan_to_num(pw, nan=0.0, posinf=0.0, neginf=0.0)
                if pw.shape[0] != n_genes:
                    # try to broadcast or truncate
                    m = min(pw.shape[0], n_genes)
                    col = np.zeros(n_genes, dtype=float)
                    col[:m] = pw[:m]
                    pw = col
            else:
                pw = np.zeros(n_genes, dtype=float)

            out[i, :, 0] = ess * pw

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
