import numpy as np
from genemila.features.api import Feature, register

@register
class AdditiveTimesNTranscripts(Feature):
    name = "additive_times_n_transcripts_e453"
    version = 1
    description = "Elementwise product of additive_response and n_transcripts of gene g."
    rationale = ("Genes with more transcript isoforms may have more complex regulatory "
                 "responses; scaling the additive baseline by n_transcripts captures "
                 "response heterogeneity tied to regulatory complexity.")
    inputs = ["gene_annotation", "additive_response"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        n_perts = len(perts)

        # Fetch additive_response feature (n_perts, n_genes, dim)
        add = ctx.feature("additive_response", perts)
        add = np.asarray(add, dtype=float)
        if add.ndim == 2:
            add = add[:, :, None]

        # Build n_transcripts vector aligned to ctx.genes
        ntx = np.ones(n_genes, dtype=float)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes_ann = ann.get("genes", {})
            cols = ann.get("columns", [])
            try:
                idx = cols.index("n_transcripts")
            except ValueError:
                idx = None
            if idx is not None:
                for gi, g in enumerate(ctx.genes):
                    vals = genes_ann.get(g)
                    if vals is None:
                        continue
                    try:
                        v = vals[idx]
                    except (IndexError, TypeError):
                        continue
                    if v is not None:
                        ntx[gi] = float(v)

        out = np.zeros((n_perts, n_genes, 1), dtype=float)
        for i in range(n_perts):
            out[i, :, 0] = add[i, :, 0] * ntx

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
