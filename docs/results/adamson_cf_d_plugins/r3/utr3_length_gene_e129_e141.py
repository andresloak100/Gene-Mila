import numpy as np
from genemila.features.api import Feature, register


@register
class Utr3LengthGene(Feature):
    name = "utr3_length_gene_e129_e141"
    version = 1
    description = "log10 of the 3' UTR length of gene g from gene_annotation, median-imputed."
    rationale = ("Longer 3' UTRs carry more miRNA binding sites and affect mRNA stability, "
                 "dampening post-transcriptional response to perturbation.")
    inputs = ["knowledge:gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1))

        ann = ctx.knowledge("gene_annotation")
        vals = np.full(ctx.n_genes, np.nan, dtype=float)

        if ann is not None:
            cols = ann.get("columns", [])
            genes_tbl = ann.get("genes", {})
            try:
                idx = cols.index("utr3_length")
            except ValueError:
                idx = None
            if idx is not None:
                for g, row in genes_tbl.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None:
                        continue
                    try:
                        v = row[idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        v = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(v) and v > 0:
                        vals[gi] = v

        # log10 transform, impute missing with median of observed
        obs = np.isfinite(vals) & (vals > 0)
        if obs.any():
            logged = np.log10(vals[obs])
            med = float(np.median(logged))
            feat = np.full(ctx.n_genes, med, dtype=float)
            feat[obs] = logged
        else:
            feat = np.zeros(ctx.n_genes, dtype=float)

        feat = np.nan_to_num(feat, nan=0.0, posinf=0.0, neginf=0.0)
        out[:, :, 0] = feat[None, :]
        return out
