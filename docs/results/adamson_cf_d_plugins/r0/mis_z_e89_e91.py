import numpy as np
from genemila.features.api import Feature, FeatureContext, register


@register
class MisZScore(Feature):
    name = "mis_z_e89_e91"
    version = 1
    description = "Missense z-score (mis_z) for gene g from gene_constraint, broadcast across perturbations."
    rationale = ("High missense constraint (mis_z) indicates strong purifying selection against "
                 "missense variants, marking functionally important genes whose perturbation may "
                 "produce larger transcriptomic changes.")
    inputs = ["gene_constraint"]
    params = {}
    dim = 1

    def compute(self, ctx: FeatureContext, perts: list[str], params: dict) -> np.ndarray:
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        knowledge = ctx.knowledge("gene_constraint")
        if knowledge is None:
            return out

        columns = knowledge.get("columns", [])
        try:
            mis_idx = columns.index("mis_z")
        except ValueError:
            return out

        genes_table = knowledge.get("genes", {}) or {}

        vec = np.full(ctx.n_genes, np.nan, dtype=float)
        for g, col in ctx.gene_index.items():
            vals = genes_table.get(g)
            if vals is None:
                continue
            try:
                v = vals[mis_idx]
            except (IndexError, TypeError):
                continue
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv):
                vec[col] = fv

        # Fill missing with 0 so output is finite; broadcast across perturbations.
        vec = np.where(np.isfinite(vec), vec, 0.0)
        out[:, :, 0] = vec[None, :]
        return out
