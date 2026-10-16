import numpy as np
from genemila.features.api import Feature, register


@register
class ScreenDeltaOverTranscriptLength(Feature):
    name = "screen_delta_over_transcript_length_e546"
    version = 1
    description = "Signed Replogle screen delta of the perturbation's target divided by transcript_length of the target gene."
    rationale = "Dividing signed Replogle screen delta by transcript length normalizes for gene size and may improve the screen delta feature."
    inputs = ["knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        if ann is None:
            return out
        genes_map = ann.get("genes") if isinstance(ann, dict) else None
        if not genes_map:
            return out
        columns = ann.get("columns", []) if isinstance(ann, dict) else []
        try:
            tl_idx = columns.index("transcript_length")
        except ValueError:
            return out

        # transcript length per bundle gene (nan -> 0, negatives -> 0)
        tl = np.zeros(ctx.n_genes, dtype=float)
        for gi, g in enumerate(ctx.genes):
            vals = genes_map.get(g)
            if vals is None:
                continue
            v = vals[tl_idx]
            if v is None:
                continue
            try:
                fv = float(v)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fv) and fv > 0:
                tl[gi] = fv

        # Replogle signed screen deltas
        rep = ctx.knowledge("replogle2022_k562")
        if not isinstance(rep, dict):
            return out
        sign = rep.get("sign", -1)
        try:
            sign = float(sign)
        except (TypeError, ValueError):
            sign = -1.0
        rep_perts = rep.get("perts") or {}
        rep_genes = rep.get("genes") or []
        # map bundle gene name -> index in replogle genes vector
        rep_gene_pos = {}
        for j, rg in enumerate(rep_genes):
            if rg not in rep_gene_pos:
                rep_gene_pos[rg] = j

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue
            acc = np.zeros(ctx.n_genes, dtype=float)
            any_hit = False
            for tg in targets:
                rec = rep_perts.get(tg)
                if rec is None:
                    continue
                delta = rec.get("delta") if isinstance(rec, dict) else None
                if delta is None:
                    continue
                # find transcript length of the target gene itself
                tgi = ctx.gene_index.get(tg)
                if tgi is None:
                    continue
                tlen = tl[tgi]
                if tlen <= 0:
                    continue
                j = rep_gene_pos.get(tg)
                if j is None:
                    continue
                try:
                    dv = float(delta[j])
                except (TypeError, ValueError, IndexError):
                    continue
                if not np.isfinite(dv):
                    continue
                acc += (sign * dv) / tlen
                any_hit = True
            if any_hit:
                out[i, :, 0] = acc

        out[~np.isfinite(out)] = 0.0
        return out
