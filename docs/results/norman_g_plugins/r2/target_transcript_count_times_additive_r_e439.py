import numpy as np
from genemila.features.api import Feature, register


@register
class TargetTranscriptCountTimesAdditiveR(Feature):
    name = "target_transcript_count_times_additive_r_e439"
    version = 1
    description = "Product of the mean transcript count of p's target genes and additive_response."
    rationale = ("Transcript count reflects isoform diversity and may affect CRISPRa efficiency; "
                 "multiplying it by the additive baseline scales the response by target complexity.")
    inputs = ["knowledge", "feature"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        # Precompute per-gene transcript counts from gene_annotation knowledge.
        cache = ctx.cache
        if "e439_n_transcripts" not in cache:
            ann = ctx.knowledge("gene_annotation")
            vec = np.ones(n_genes, dtype=float)
            if ann is not None:
                cols = ann.get("columns", [])
                try:
                    idx = cols.index("n_transcripts")
                except ValueError:
                    idx = 1
                genes_map = ann.get("genes", {}) or {}
                for g, gi in ctx.gene_index.items():
                    vals = genes_map.get(g)
                    if vals is not None and idx < len(vals) and vals[idx] is not None:
                        try:
                            v = float(vals[idx])
                            if np.isfinite(v):
                                vec[gi] = v
                        except (TypeError, ValueError):
                            pass
            cache["e439_n_transcripts"] = vec
        ntrans = cache["e439_n_transcripts"]

        # Additive baseline for all perturbations (composition, no leakage inside it
        # is handled by that feature; we just reuse its output).
        try:
            add = ctx.feature("additive_response", perts)
        except Exception:
            add = None

        for i, p in enumerate(perts):
            tidx = ctx.target_indices(p)
            if len(tidx) > 0:
                mean_tc = float(np.mean(ntrans[tidx]))
            else:
                mean_tc = 1.0
            if add is not None:
                base = add[i, :, 0]
            else:
                base = np.zeros(n_genes, dtype=float)
            out[i, :, 0] = mean_tc * base

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
