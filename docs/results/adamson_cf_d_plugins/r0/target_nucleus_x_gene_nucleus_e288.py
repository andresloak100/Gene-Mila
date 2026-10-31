import numpy as np
from genemila.features.api import Feature, register


@register
class TargetNucleusXGeneNucleusE288(Feature):
    name = "target_nucleus_x_gene_nucleus_e288"
    version = 1
    description = (
        "Indicator that the perturbation target's protein is annotated as nuclear "
        "(protein_annotation) multiplied by an indicator that gene g's protein is "
        "also annotated as nuclear."
    )
    rationale = (
        "Nuclear proteins often interact; perturbing one nuclear protein may affect "
        "the expression of genes encoding other nuclear proteins."
    )
    inputs = ["protein_annotation", "target_indices"]
    params = {}
    dim = 1

    def _nucleus_vector(self, ctx):
        """Return (n_genes,) 0/1 array: 1 if gene's protein has nucleus flag."""
        cache = ctx.cache
        key = "_e288_nucleus_vec"
        if key in cache:
            return cache[key]

        vec = np.zeros(ctx.n_genes, dtype=np.float64)
        pa = ctx.knowledge("protein_annotation")
        if pa is not None:
            columns = pa.get("columns", [])
            genes = pa.get("genes", {}) or {}
            try:
                nuc_idx = columns.index("nucleus")
            except ValueError:
                nuc_idx = None
            if nuc_idx is not None:
                for g, vals in genes.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None or vals is None:
                        continue
                    try:
                        v = vals[nuc_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        vec[gi] = 1.0 if float(v) > 0.5 else 0.0
                    except (TypeError, ValueError):
                        continue
        cache[key] = vec
        return vec

    def compute(self, ctx, perts, params):
        nuc_vec = self._nucleus_vector(ctx)
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=np.float64)

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            # target is nuclear if any of its targeted genes is nuclear
            tgt_nuc = 0.0
            for ti in tgt_idx:
                if 0 <= ti < ctx.n_genes and nuc_vec[ti] > 0.5:
                    tgt_nuc = 1.0
                    break
            if tgt_nuc > 0.5:
                out[i, :, 0] = nuc_vec

        return out
