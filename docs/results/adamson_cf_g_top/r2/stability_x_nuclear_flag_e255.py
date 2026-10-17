import numpy as np
from genemila.features.api import Feature, register


@register
class StabilityXNuclearFlagE255(Feature):
    name = "stability_x_nuclear_flag_e255"
    version = 1
    description = (
        "Element-wise product of the protein-stability proxy and a binary flag "
        "indicating whether the perturbation's target protein is annotated as nuclear."
    )
    rationale = (
        "Stable nuclear proteins may amplify transcriptional responses; the interaction "
        "of stability and nuclear localization could be more predictive than either alone."
    )
    inputs = ["control_cells", "protein_annotation"]
    params = {"stability_feature": "protein_stability_proxy_e81", "compartment": "nucleus"}
    dim = 1

    def compute(self, ctx, perts, params):
        stability_feature = params.get("stability_feature", "protein_stability_proxy_e81")
        compartment = params.get("compartment", "nucleus")

        n_perts = len(perts)
        n_genes = ctx.n_genes

        # Stability proxy per gene: shape (n_genes,)
        stab = ctx.feature(stability_feature, perts, params=None)
        stab = np.asarray(stab, dtype=float)
        if stab.ndim == 3:
            stab = stab[:, :, 0]
        # Reduce to a per-gene vector (average over perturbations if needed).
        if stab.ndim == 2:
            stab_vec = stab.mean(axis=0)
        else:
            stab_vec = stab.reshape(-1)
        if stab_vec.shape[0] != n_genes:
            # Fallback: pad/truncate safely.
            vec = np.zeros(n_genes, dtype=float)
            m = min(n_genes, stab_vec.shape[0])
            vec[:m] = stab_vec[:m]
            stab_vec = vec
        stab_vec = np.nan_to_num(stab_vec, nan=0.0, posinf=0.0, neginf=0.0)

        # Nuclear flag per gene from protein_annotation.
        nuclear_flag = np.zeros(n_genes, dtype=float)
        ann = ctx.knowledge("protein_annotation")
        if ann is not None and isinstance(ann, dict):
            genes_map = ann.get("genes", {})
            columns = ann.get("columns", [])
            # Locate the compartment column index (default to nucleus).
            comp_col = compartment
            idx = None
            for j, c in enumerate(columns):
                if c == comp_col:
                    idx = j
                    break
            if idx is not None:
                for g, vals in genes_map.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None:
                        continue
                    if vals is None:
                        continue
                    try:
                        v = vals[idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        nuclear_flag[gi] = 1.0 if float(v) > 0 else 0.0
                    except (TypeError, ValueError):
                        continue

        # Per-gene product.
        prod = stab_vec * nuclear_flag  # (n_genes,)

        # Broadcast to (n_perts, n_genes, 1) using the target's nuclear flag.
        out = np.zeros((n_perts, n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if len(t_idx) == 0:
                continue
            # Use the first target's nuclear flag (single-gene targets).
            flag = nuclear_flag[t_idx[0]]
            if flag > 0:
                out[i, :, 0] = prod
            else:
                out[i, :, 0] = 0.0

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
