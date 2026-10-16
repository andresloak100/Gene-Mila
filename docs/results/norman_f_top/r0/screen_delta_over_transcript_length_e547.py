import numpy as np
from genemila.features.api import Feature, register


@register
class ScreenDeltaOverTranscriptLength(Feature):
    name = "screen_delta_over_transcript_length_e547"
    version = 1
    description = "Signed Replogle screen delta of the perturbation's target divided by transcript_length of the target gene."
    rationale = "Dividing signed Replogle screen delta by transcript length normalizes for gene size and may improve the screen delta feature."
    inputs = ["knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))

        ann = ctx.knowledge("gene_annotation")
        if ann is None:
            return out
        genes_ann = ann.get("genes", {})
        columns = ann.get("columns", [])
        try:
            tl_idx = columns.index("transcript_length")
        except ValueError:
            return out

        rep = ctx.knowledge("replogle2022_k562")
        if rep is None:
            return out
        sign = rep.get("sign", -1)
        rep_perts = rep.get("perts", {})

        def tlen(gene):
            v = genes_ann.get(gene)
            if v is None:
                return None
            try:
                x = v[tl_idx]
            except (IndexError, TypeError):
                return None
            if x is None:
                return None
            try:
                x = float(x)
            except (TypeError, ValueError):
                return None
            if not np.isfinite(x) or x <= 0:
                return None
            return x

        def rep_delta(gene):
            entry = rep_perts.get(gene)
            if entry is None:
                return None
            d = entry.get("delta") if isinstance(entry, dict) else None
            if d is None:
                return None
            return np.asarray(d, dtype=float) * float(sign)

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue
            acc = np.zeros(ctx.n_genes, dtype=float)
            any_ok = False
            for t in targets:
                tl = tlen(t)
                if tl is None:
                    continue
                d = rep_delta(t)
                if d is None:
                    continue
                if d.shape[0] != ctx.n_genes:
                    continue
                acc += d / tl
                any_ok = True
            if any_ok:
                out[i, :, 0] = acc

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
