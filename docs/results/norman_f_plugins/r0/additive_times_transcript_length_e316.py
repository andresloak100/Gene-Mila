import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveTimesTranscriptLength(Feature):
    name = "additive_times_transcript_length_e316"
    version = 1
    description = "Elementwise product of additive_response and transcript_length of gene g."
    rationale = ("Longer transcripts may harbour more regulatory elements and thus respond "
                 "differently to perturbation; scaling the additive baseline by transcript "
                 "length could capture gene-specific amplification or attenuation.")
    inputs = ["gene_annotation", "additive_response"]
    params = {}
    dim = 1

    def _transcript_length(self, ctx):
        cached = ctx.cache.get("_atl_transcript_length")
        if cached is not None:
            return cached
        vec = np.ones(ctx.n_genes, dtype=float)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            cols = ann.get("columns", [])
            units = ann.get("column_units", {})
            idx = None
            for j, c in enumerate(cols):
                if c == "transcript_length":
                    idx = j
                    break
            if idx is None:
                for j, c in enumerate(cols):
                    if "transcript_length" in str(c):
                        idx = j
                        break
            genes = ann.get("genes", {})
            if idx is not None:
                for g in ctx.genes:
                    row = genes.get(g)
                    if row is None:
                        continue
                    try:
                        v = row[idx]
                    except (TypeError, IndexError):
                        continue
                    if v is None:
                        continue
                    try:
                        v = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(v):
                        vec[ctx.gene_index[g]] = v
        ctx.cache["_atl_transcript_length"] = vec
        return vec

    def compute(self, ctx, perts, params):
        tl = self._transcript_length(ctx)
        add = ctx.feature("additive_response", perts, params=None)
        add = np.asarray(add, dtype=float)
        if add.ndim == 3:
            add = add[:, :, 0]
        elif add.ndim == 1:
            add = add[None, :]
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)
        n = min(add.shape[0], len(perts))
        block = add[:n] * tl[None, :]
        out[:n, :, 0] = np.nan_to_num(block, nan=0.0, posinf=0.0, neginf=0.0)
        return out
