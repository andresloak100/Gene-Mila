import numpy as np
from genemila.features.api import Feature, register


@register
class MissenseConstraintFeaturesE57(Feature):
    name = "missense_constraint_features_e57"
    version = 1
    description = "Standardized per-gene missense constraint features (oe_mis, oe_mis_upper, mis_z)."
    rationale = (
        "Missense constraint reflects functional importance and dosage sensitivity, "
        "which correlates with magnitude and direction of expression response to perturbations."
    )
    inputs = ["knowledge:gene_constraint"]
    params = {}
    dim = 3

    _COLUMNS = ("oe_mis", "oe_mis_upper", "mis_z")

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        n_genes = ctx.n_genes

        cache = ctx.cache
        key = ("missense_constraint_features_e57", "gene_matrix")
        if key in cache:
            gene_matrix = cache[key]
        else:
            gene_matrix = np.full((n_genes, len(self._COLUMNS)), np.nan, dtype=float)

            kc = ctx.knowledge("gene_constraint")
            if kc is not None:
                genes_map = kc.get("genes", {}) if isinstance(kc, dict) else {}
                columns = kc.get("columns", []) if isinstance(kc, dict) else []

                # Resolve column indices robustly.
                col_idx = []
                for cname in self._COLUMNS:
                    if cname in columns:
                        col_idx.append(columns.index(cname))
                    else:
                        col_idx.append(None)

                for gi, gene in enumerate(ctx.genes):
                    vals = genes_map.get(gene)
                    if vals is None:
                        continue
                    for j, ci in enumerate(col_idx):
                        if ci is None:
                            continue
                        try:
                            v = vals[ci]
                        except (IndexError, TypeError):
                            continue
                        if v is None:
                            continue
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv):
                            gene_matrix[gi, j] = fv

            # Standardize each column across genes, ignoring NaNs.
            for j in range(gene_matrix.shape[1]):
                col = gene_matrix[:, j]
                mask = np.isfinite(col)
                if not mask.any():
                    gene_matrix[:, j] = 0.0
                    continue
                vals = col[mask]
                mu = vals.mean()
                sd = vals.std()
                if not np.isfinite(sd) or sd <= 0.0:
                    gene_matrix[mask, j] = 0.0
                else:
                    gene_matrix[mask, j] = (vals - mu) / sd
                gene_matrix[~mask, j] = 0.0

            cache[key] = gene_matrix

        out = np.empty((n_perts, n_genes, self.dim), dtype=float)
        for i in range(n_perts):
            out[i] = gene_matrix

        # Ensure finiteness.
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
