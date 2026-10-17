import numpy as np
from genemila.features.api import Feature, register


@register
class TargetEssentialityXCoexpression(Feature):
    name = "target_essentiality_x_coexpression_e638"
    version = 1
    description = "Product of target gene essentiality (from gnomAD LoF constraint) and the Pearson coexpression between target and gene g across control cells."
    rationale = "Essential genes are hubs; their activity is coupled to genes coexpressed with them, so the interaction of target essentiality with local coexpression may predict the response magnitude."
    inputs = ["control_cells", "gene_corr", "gene_constraint"]
    params = {"essentiality_source": "depmap"}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # Build per-gene essentiality score from gnomAD LoF constraint (LOEUF).
        # Low LOEUF => LoF-intolerant => essential-like. Use -log(LOEUF) clipped.
        ess = np.zeros(n_genes, dtype=float)
        constraint = ctx.knowledge("gene_constraint")
        if constraint is not None:
            cols = constraint.get("columns", [])
            try:
                loeuf_idx = cols.index("oe_lof_upper")
            except ValueError:
                loeuf_idx = None
            genes_tbl = constraint.get("genes", {})
            for g, vals in genes_tbl.items():
                gi = ctx.gene_index.get(g)
                if gi is None:
                    continue
                if loeuf_idx is None or vals is None:
                    continue
                v = vals[loeuf_idx]
                if v is None:
                    continue
                try:
                    v = float(v)
                except (TypeError, ValueError):
                    continue
                if not np.isfinite(v) or v <= 0.0:
                    continue
                ess[gi] = -np.log(max(v, 1e-3))

        # Center essentiality to keep products well-scaled
        if ess.size and np.any(ess != 0.0):
            ess = ess - ess.mean()

        gene_corr = ctx.gene_corr
        if gene_corr is None:
            return out

        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if not t_idx:
                continue
            # If multiple targets, average their essentiality and coexpression rows
            t_ess = np.mean([ess[t] for t in t_idx])
            coexpr = gene_corr[t_idx, :].mean(axis=0)
            coexpr = np.nan_to_num(coexpr, nan=0.0, posinf=0.0, neginf=0.0)
            out[i, :, 0] = t_ess * coexpr

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
