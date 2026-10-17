import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveResponseXTargetProteinLength(Feature):
    name = "additive_response_x_target_protein_lengt_e657"
    version = 1
    description = ("Product of additive_response (sum over target genes of the "
                   "additive baseline prediction) and the mean protein length of "
                   "the perturbation's target genes.")
    rationale = ("Longer proteins may have more interaction interfaces, so the "
                 "additive response could be amplified for perturbations whose "
                 "targets encode long proteins.")
    inputs = ["protein_annotation", "control_cells"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        # --- load protein lengths ---
        prot = ctx.knowledge("protein_annotation")
        plen_by_gene = {}
        if prot is not None:
            cols = prot.get("columns", [])
            genes_tbl = prot.get("genes", {})
            try:
                idx = cols.index("protein_length")
            except ValueError:
                idx = 0
            for sym, vals in genes_tbl.items():
                if vals is None:
                    continue
                try:
                    v = vals[idx]
                except Exception:
                    continue
                if v is None:
                    continue
                try:
                    fv = float(v)
                except (TypeError, ValueError):
                    continue
                if np.isfinite(fv):
                    plen_by_gene[sym] = fv

        # --- additive baseline: sum over target genes of control_mean ---
        control_mean = np.asarray(ctx.control_mean, dtype=float)

        # cache additive response per perturbation id (exclude handled per p)
        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if len(tgt_idx) == 0:
                add_resp = np.zeros(ctx.n_genes, dtype=float)
            else:
                add_resp = control_mean[tgt_idx].sum()

            tgt_genes = ctx.target_genes(p)
            lens = [plen_by_gene[g] for g in tgt_genes if g in plen_by_gene]
            if len(lens) > 0:
                mean_len = float(np.mean(lens))
            else:
                mean_len = 0.0

            out[i, :, 0] = add_resp * mean_len

        # ensure finite
        out[~np.isfinite(out)] = 0.0
        return out
