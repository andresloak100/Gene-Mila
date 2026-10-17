import numpy as np
from genemila.features.api import Feature, register


@register
class NuclearTargetXNuclearGene(Feature):
    name = "nuclear_target_x_nuclear_gene_e493"
    version = 1
    description = "Indicator product: 1 if both target and gene encode nuclear proteins, else 0."
    rationale = ("Nuclear proteins often regulate transcription; perturbing them may "
                 "preferentially affect other nuclear genes.")
    inputs = ["protein_annotation", "targets"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        pa = ctx.knowledge("protein_annotation")
        if not pa:
            return out

        cols = pa.get("columns", [])
        genes_map = pa.get("genes", {})
        try:
            nuc_idx = cols.index("nucleus")
        except ValueError:
            return out

        # Gene-level nuclear indicator
        gene_nuc = np.zeros(ctx.n_genes, dtype=float)
        for i, g in enumerate(ctx.genes):
            vals = genes_map.get(g)
            if vals is None:
                continue
            try:
                v = vals[nuc_idx]
            except (IndexError, TypeError):
                continue
            if v is not None and float(v) > 0:
                gene_nuc[i] = 1.0

        for i, p in enumerate(perts):
            tgt_nuc = 0.0
            for tg in ctx.target_genes(p):
                vals = genes_map.get(tg)
                if vals is None:
                    continue
                try:
                    v = vals[nuc_idx]
                except (IndexError, TypeError):
                    continue
                if v is not None and float(v) > 0:
                    tgt_nuc = 1.0
                    break
            if tgt_nuc > 0:
                out[i, :, 0] = gene_nuc

        return out
