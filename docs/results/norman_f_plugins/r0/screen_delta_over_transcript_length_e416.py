import numpy as np
from genemila.features.api import Feature, register


@register
class ScreenDeltaOverTranscriptLength(Feature):
    name = "screen_delta_over_transcript_length_e416"
    version = 1
    description = ("Signed Replogle2022 K562 CRISPRi screen delta summed over the "
                   "perturbation's target gene(s), divided by the transcript length "
                   "of gene g from gene_annotation.")
    rationale = ("Transcript length affects baseline expression and stability; "
                 "dividing the screen delta by it creates a rate-like feature that "
                 "may be more comparable across genes.")
    inputs = ["knowledge:gene_annotation", "knowledge:replogle2022_k562"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        n_perts = len(perts)

        # --- transcript length per gene (fallback to 1.0 where missing) ---
        tlen = np.ones(n_genes, dtype=np.float64)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes = ann.get("genes", {})
            cols = ann.get("columns", [])
            try:
                idx = cols.index("transcript_length")
            except ValueError:
                idx = None
            if idx is not None:
                for i, g in enumerate(ctx.genes):
                    vals = genes.get(g)
                    if vals is not None:
                        try:
                            v = vals[idx]
                        except (IndexError, TypeError):
                            v = None
                        if v is not None:
                            try:
                                fv = float(v)
                            except (TypeError, ValueError):
                                fv = 0.0
                            if np.isfinite(fv) and fv > 0.0:
                                tlen[i] = fv
        inv_tlen = 1.0 / tlen  # (n_genes,)

        # --- signed screen delta per gene (scalar per perturbation) ---
        screen = np.zeros(n_perts, dtype=np.float64)
        rep = ctx.knowledge("replogle2022_k562")
        if rep is not None:
            sign = rep.get("sign", -1)
            try:
                sign = float(sign)
            except (TypeError, ValueError):
                sign = -1.0
            rgenes = rep.get("genes", None)
            rperts = rep.get("perts", None)
            if rgenes is not None and rperts is not None:
                rindex = {}
                for j, g in enumerate(rgenes):
                    if g not in rindex:
                        rindex[g] = j
                for i, p in enumerate(perts):
                    tg = ctx.target_genes(p)
                    if not tg:
                        continue
                    total = 0.0
                    found = False
                    for g in tg:
                        entry = rperts.get(g)
                        if entry is None:
                            continue
                        delta = entry.get("delta", None)
                        if delta is None:
                            continue
                        if isinstance(delta, (list, tuple, np.ndarray)):
                            arr = np.asarray(delta, dtype=np.float64).ravel()
                            if arr.size == len(rgenes):
                                j = rindex.get(g)
                                if j is not None and np.isfinite(arr[j]):
                                    total += sign * float(arr[j])
                                    found = True
                                    continue
                            finite = arr[np.isfinite(arr)]
                            if finite.size:
                                total += sign * float(finite.mean())
                                found = True
                        else:
                            try:
                                fv = float(delta)
                            except (TypeError, ValueError):
                                continue
                            if np.isfinite(fv):
                                total += sign * fv
                                found = True
                    if found:
                        screen[i] = total

        # screen: (n_perts,), inv_tlen: (n_genes,) -> (n_perts, n_genes)
        out = screen[:, None] * inv_tlen[None, :]
        out = out[:, :, None]  # (n_perts, n_genes, 1)
        out[~np.isfinite(out)] = 0.0
        return out
