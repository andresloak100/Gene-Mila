import numpy as np
from genemila.features.api import Feature, register


@register
class TargetProteinLengthRatioTimesAdditiveE517(Feature):
    name = "target_protein_length_ratio_times_additi_e517"
    version = 1
    description = ("Product of additive_response and the ratio (max/min) of protein "
                   "lengths of p's target genes (for single gene, ratio=1).")
    rationale = ("Pairs whose two targets differ strongly in protein size may show "
                 "asymmetric dosage effects; the max/min protein-length ratio "
                 "interacting with the additive baseline captures this non-additivity.")
    inputs = ["protein_annotation", "additive_response"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        # additive_response is shared across perturbations; compute once.
        add = ctx.feature("additive_response", perts)
        add = np.asarray(add, dtype=float)
        if add.ndim == 3:
            add2 = add[:, :, 0]
        elif add.ndim == 2:
            add2 = add
        else:
            add2 = np.broadcast_to(add.reshape(len(perts), -1), (len(perts), ctx.n_genes))

        # Load protein annotation protein_length.
        pa = ctx.knowledge("protein_annotation")
        prot_len = {}
        if pa is not None:
            cols = pa.get("columns", [])
            genes_map = pa.get("genes", {}) or {}
            try:
                li = cols.index("protein_length")
            except (ValueError, AttributeError):
                li = 0
            for g, vals in genes_map.items():
                if vals is None:
                    continue
                try:
                    v = vals[li]
                except (IndexError, TypeError):
                    continue
                if v is None:
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv):
                    prot_len[g] = fv

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            ratio = 1.0
            if tg is not None and len(tg) >= 2:
                lens = [prot_len.get(g) for g in tg]
                lens = [x for x in lens if x is not None and x > 0]
                if len(lens) >= 2:
                    mx = max(lens)
                    mn = min(lens)
                    if mn > 0:
                        ratio = mx / mn
            out[i, :, 0] = ratio * add2[i, :]

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
