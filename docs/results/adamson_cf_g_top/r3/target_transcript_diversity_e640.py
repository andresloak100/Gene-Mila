import numpy as np
from genemila.features.api import Feature, register


@register
class TargetTranscriptDiversityE640(Feature):
    name = "target_transcript_diversity_e640"
    version = 1
    description = "Transcript count of the perturbation target divided by gene span (kb)."
    rationale = (
        "Transcriptional complexity of the target gene may shape the breadth and "
        "magnitude of its perturbation response; genes with more transcripts per kb "
        "may be more tissue-specific and tightly regulated."
    )
    inputs = ["control_cells"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is None:
            return out

        columns = ann.get("columns", [])
        try:
            i_nt = columns.index("n_transcripts")
            i_span = columns.index("gene_span_kb")
        except ValueError:
            return out

        genes_tbl = ann.get("genes", {}) or {}

        # Compute diversity for all annotated genes, gather valid values.
        div_map = {}
        for sym, vals in genes_tbl.items():
            if vals is None:
                continue
            try:
                nt = vals[i_nt]
                span = vals[i_span]
            except (IndexError, TypeError):
                continue
            if nt is None or span is None:
                continue
            try:
                nt = float(nt)
                span = float(span)
            except (TypeError, ValueError):
                continue
            if not np.isfinite(nt) or not np.isfinite(span) or span <= 0:
                continue
            div_map[sym] = nt / span

        if div_map:
            med = float(np.median(np.array(list(div_map.values()), dtype=float)))
        else:
            med = 0.0

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            val = med
            for t in targets:
                if t in div_map:
                    val = div_map[t]
                    break
            out[i, :, 0] = val

        return out
