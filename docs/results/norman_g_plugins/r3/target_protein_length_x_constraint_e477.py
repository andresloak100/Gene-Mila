import numpy as np
from genemila.features.api import Feature, register


@register
class TargetProteinLengthXConstraintE477(Feature):
    name = "target_protein_length_x_constraint_e477"
    version = 1
    description = "Product of mean target protein length and pair_target_constraint_aggregate_e433."
    rationale = ("Protein length modulates how strongly target LoF-constraint aggregates "
                 "translate into perturbation response.")
    inputs = ["knowledge", "feature"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))

        # Existing constraint aggregate feature
        agg = ctx.feature("pair_target_constraint_aggregate_e433", perts)
        agg = np.asarray(agg, dtype=float)
        if agg.ndim == 2:
            agg = agg[:, :, None]
        agg = agg[:, :, 0]

        # Protein length per gene
        prot = ctx.knowledge("protein_annotation")
        mean_len = np.zeros(len(perts), dtype=float)
        if prot is not None and isinstance(prot, dict):
            cols = prot.get("columns", [])
            try:
                plen_idx = cols.index("protein_length")
            except ValueError:
                plen_idx = 0
            genes_tbl = prot.get("genes", {}) or {}
            for i, p in enumerate(perts):
                tg = ctx.target_genes(p)
                vals = []
                for g in tg:
                    v = genes_tbl.get(g)
                    if v is None:
                        continue
                    try:
                        x = v[plen_idx]
                    except (IndexError, TypeError):
                        continue
                    if x is None:
                        continue
                    try:
                        xf = float(x)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(xf):
                        vals.append(xf)
                if vals:
                    mean_len[i] = np.mean(vals)

        # Normalize mean length to a reasonable scale to keep coefficients sane
        mean_len = mean_len / 1000.0

        out[:, :, 0] = mean_len[:, None] * agg
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
