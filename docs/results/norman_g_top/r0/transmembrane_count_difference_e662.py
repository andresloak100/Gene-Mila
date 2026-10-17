import numpy as np
from genemila.features.api import Feature, register


@register
class TransmembraneCountDifference(Feature):
    name = "transmembrane_count_difference_e662"
    version = 1
    description = "Absolute difference between gene g's n_transmembrane and the mean n_transmembrane of p's targets."
    rationale = "Perturbation targets with transmembrane domains may induce responses in genes with similar membrane topology."
    inputs = ["protein_annotation", "target_genes"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        ann = ctx.knowledge("protein_annotation")
        if ann is None or "genes" not in ann or "columns" not in ann:
            return out

        cols = list(ann["columns"])
        if "n_transmembrane" not in cols:
            return out
        tm_col = cols.index("n_transmembrane")

        gene_vals = ann["genes"]
        # Build per-gene n_transmembrane array aligned to ctx.genes; missing -> 0.0
        tm = np.zeros(n_genes, dtype=float)
        for i, g in enumerate(ctx.genes):
            vals = gene_vals.get(g)
            if vals is None:
                continue
            try:
                v = vals[tm_col]
            except (IndexError, TypeError):
                continue
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv):
                tm[i] = fv

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            if not tg:
                # no targets -> difference from 0 baseline
                out[i, :, 0] = np.abs(tm)
                continue
            idx = [ctx.gene_index[g] for g in tg if g in ctx.gene_index]
            if not idx:
                out[i, :, 0] = np.abs(tm)
                continue
            target_mean = float(tm[idx].mean())
            out[i, :, 0] = np.abs(tm - target_mean)

        out[~np.isfinite(out)] = 0.0
        return out
