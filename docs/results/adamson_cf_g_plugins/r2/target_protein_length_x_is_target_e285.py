import numpy as np
from genemila.features.api import Feature, register


@register
class TargetProteinLengthXIsTarget(Feature):
    name = "target_protein_length_x_is_target_e285"
    version = 1
    description = "Product of target gene's protein length (from protein_annotation) and is_target."
    rationale = (
        "Longer proteins may be more sensitive to perturbations (misfolding/aggregation), "
        "so scaling the is_target indicator by the target's protein length captures "
        "target-specific sensitivity."
    )
    inputs = ["protein_annotation", "control_cells"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        n_genes = ctx.n_genes
        out = np.zeros((n_perts, n_genes, 1), dtype=float)

        # Load protein length per gene once.
        lengths = np.zeros(n_genes, dtype=float)
        prot = ctx.knowledge("protein_annotation")
        if prot is not None:
            cols = prot.get("columns", [])
            try:
                pl_idx = cols.index("protein_length")
            except ValueError:
                pl_idx = 0
            genes = prot.get("genes", {}) or {}
            for g, vals in genes.items():
                gi = ctx.gene_index.get(g)
                if gi is None or vals is None:
                    continue
                try:
                    v = vals[pl_idx]
                except (IndexError, TypeError):
                    continue
                if v is None:
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv):
                    lengths[gi] = fv

        for i, p in enumerate(perts):
            tidx = ctx.target_indices(p)
            if not tidx:
                continue
            for t in tidx:
                out[i, t, 0] = lengths[t]

        out[~np.isfinite(out)] = 0.0
        return out
