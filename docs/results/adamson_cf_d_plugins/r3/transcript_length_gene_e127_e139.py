import numpy as np
from genemila.features.api import Feature, register


@register
class TranscriptLengthGene(Feature):
    name = "transcript_length_gene_e127_e139"
    version = 1
    description = "log10 transcript length of gene g from gene_annotation, median-imputed."
    rationale = "Transcript length correlates with mRNA stability and regulatory complexity, affecting perturbation response magnitude."
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        values = np.full(n_genes, np.nan, dtype=float)

        ka = ctx.knowledge("gene_annotation")
        if ka is not None:
            cols = ka.get("columns", [])
            genes = ka.get("genes", {}) or {}
            try:
                ci = cols.index("transcript_length")
            except ValueError:
                ci = None
            if ci is not None:
                for g, col in ctx.gene_index.items():
                    row = genes.get(g)
                    if row is None:
                        continue
                    try:
                        v = row[ci]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv) and fv > 0:
                        values[col] = np.log10(fv)

        finite = np.isfinite(values)
        if finite.any():
            med = float(np.median(values[finite]))
        else:
            med = 0.0
        values[~finite] = med

        out = np.empty((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = values[None, :]
        out[~np.isfinite(out)] = 0.0
        return out
