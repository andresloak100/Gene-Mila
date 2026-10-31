import numpy as np
from genemila.features.api import Feature, register


@register
class NTranscriptsE41(Feature):
    name = "n_transcripts_e41"
    version = 1
    description = "Number of transcript isoforms for gene g from gene_annotation."
    rationale = ("Genes with more isoforms may be more dynamically regulated and respond "
                 "more strongly to perturbations.")
    inputs = ["knowledge:gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        vals = np.zeros(n_genes, dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes = ann.get("genes", {}) or {}
            columns = ann.get("columns", []) or []
            try:
                col_idx = columns.index("n_transcripts")
            except ValueError:
                col_idx = None
            if col_idx is not None:
                for g, row in genes.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None:
                        continue
                    try:
                        v = row[col_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        vals[gi] = fv

        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        out[:, :, 0] = vals[None, :]
        return out
