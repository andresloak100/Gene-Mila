import numpy as np
from genemila.features.api import Feature, register


@register
class TargetMrnaStabilityE363(Feature):
    name = "target_mrna_stability_e363"
    version = 1
    description = ("Proxy mRNA stability score for the perturbation target derived from "
                   "3'UTR length (longer 3'UTRs tend to harbour more AU-rich elements and "
                   "destabilising motifs, hence shorter half-life).")
    rationale = ("mRNA stability influences how quickly target mRNA is depleted after "
                 "CRISPRi, which may alter the dynamics of downstream responses. 3'UTR "
                 "length is a sequence-based proxy for AU-rich element content.")
    inputs = ["control_cells", "gene_annotation"]
    params = {"proxy": "utr3_length"}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))

        ann = ctx.knowledge("gene_annotation")
        # Build per-gene-target stability score (higher = less stable / shorter half-life).
        # We use -log1p(utr3_length) so that longer 3'UTR => lower (more negative) stability
        # score, i.e. shorter half-life. Missing values filled with the median.
        col_idx = None
        genes_map = None
        if isinstance(ann, dict):
            cols = ann.get("columns", [])
            try:
                col_idx = cols.index(params.get("proxy", "utr3_length"))
            except (ValueError, AttributeError):
                col_idx = None
            genes_map = ann.get("genes", None)

        # Precompute a stability value per gene symbol if annotation available.
        stability_by_symbol = {}
        if genes_map is not None and col_idx is not None:
            for sym, vals in genes_map.items():
                try:
                    v = vals[col_idx]
                except (IndexError, TypeError):
                    v = None
                if v is None:
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if not np.isfinite(fv):
                    continue
                stability_by_symbol[sym] = -np.log1p(max(fv, 0.0))

        # Median fill value from the computed stability scores.
        if len(stability_by_symbol) > 0:
            fill = float(np.median(np.fromiter(stability_by_symbol.values(), dtype=float)))
        else:
            fill = 0.0

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            if len(tg) == 0:
                out[i, :, 0] = fill
                continue
            vals = [stability_by_symbol.get(g, fill) for g in tg]
            score = float(np.mean(vals))
            if not np.isfinite(score):
                score = fill
            out[i, :, 0] = score

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
