import numpy as np
from genemila.features.api import Feature, register


@register
class AAHydrophobicFractionGeneE99(Feature):
    name = "aa_hydrophobic_fraction_gene_e99"
    version = 1
    description = (
        "Fraction of hydrophobic amino acids (A,V,I,L,M,F,W,P) in each gene's protein, "
        "broadcast across all perturbations."
    )
    rationale = (
        "Hydrophobic protein composition may influence co-translational folding and "
        "stress responses, affecting transcript levels upon perturbation."
    )
    inputs = ["gene_annotation"]
    params = {"aa_list": ["aa_A", "aa_V", "aa_I", "aa_L", "aa_M", "aa_F", "aa_W", "aa_P"]}
    dim = 1

    def compute(self, ctx, perts, params):
        aa_list = params.get(
            "aa_list", ["aa_A", "aa_V", "aa_I", "aa_L", "aa_M", "aa_F", "aa_W", "aa_P"]
        )

        cache_key = ("aa_hydrophobic_fraction_e99", tuple(aa_list))
        if cache_key in ctx.cache:
            gene_vals = ctx.cache[cache_key]
        else:
            gene_vals = self._compute_gene_values(ctx, aa_list)
            ctx.cache[cache_key] = gene_vals

        out = np.empty((len(perts), ctx.n_genes, 1), dtype=float)
        out[:, :, 0] = gene_vals[None, :]
        return out

    def _compute_gene_values(self, ctx, aa_list):
        n_genes = ctx.n_genes
        vals = np.full(n_genes, np.nan, dtype=float)

        ka = ctx.knowledge("gene_annotation")
        if ka is not None:
            columns = ka.get("columns", []) or []
            genes = ka.get("genes", {}) or {}
            col_idx = {c: i for i, c in enumerate(columns)}
            present = [c for c in aa_list if c in col_idx]
            if present:
                idxs = [col_idx[c] for c in present]
                for g in ctx.genes:
                    row = genes.get(g)
                    if row is None:
                        continue
                    gi = ctx.gene_index[g]
                    total = 0.0
                    ok = True
                    for j in idxs:
                        v = row[j] if j < len(row) else None
                        if v is None:
                            ok = False
                            break
                        try:
                            total += float(v)
                        except (TypeError, ValueError):
                            ok = False
                            break
                    if ok:
                        vals[gi] = total

        # Impute missing with median of observed values.
        finite_mask = np.isfinite(vals)
        if finite_mask.any():
            median = float(np.median(vals[finite_mask]))
            vals[~finite_mask] = median
        else:
            vals[:] = 0.0

        return vals
