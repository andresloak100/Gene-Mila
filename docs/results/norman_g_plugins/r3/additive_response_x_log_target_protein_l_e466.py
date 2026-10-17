import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveResponseXLogTargetProteinLength(Feature):
    name = "additive_response_x_log_target_protein_l_e466"
    version = 1
    description = "Product of additive_response and log1p of the mean protein length of the perturbation's target genes."
    rationale = "Longer proteins may have more interaction domains; a log-scaled target protein length may modulate perturbation effect strength."
    inputs = ["control_cells", "train_delta", "knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        # Load protein length per gene from protein_annotation knowledge.
        prot = ctx.knowledge("protein_annotation")
        gene_prot_len = np.full(ctx.n_genes, np.nan, dtype=float)
        if prot is not None:
            cols = list(prot.get("columns", []))
            genes_map = prot.get("genes", {})
            if "protein_length" in cols:
                pl_idx = cols.index("protein_length")
                for g, vals in genes_map.items():
                    gi = ctx.gene_index.get(g)
                    if gi is None or vals is None:
                        continue
                    v = vals[pl_idx]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        gene_prot_len[gi] = fv

        # Memoize additive response per perturbation (leakage-safe).
        cache = ctx.cache
        if "additive_response_e466" not in cache:
            cache["additive_response_e466"] = {}

        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            # Additive response: sum over target genes of each target's mean training delta.
            if p in cache["additive_response_e466"]:
                add_resp = cache["additive_response_e466"][p]
            else:
                tgt_idx = ctx.target_indices(p)
                add_resp = np.zeros(ctx.n_genes, dtype=float)
                if len(tgt_idx) > 0:
                    _, d = ctx.train_delta(exclude=p)
                    if d.shape[0] > 0:
                        mean_delta = d.mean(axis=0)
                        for gi in tgt_idx:
                            add_resp += mean_delta[gi]
                cache["additive_response_e466"][p] = add_resp

            # Mean log-scaled protein length over targets.
            tgt_idx = ctx.target_indices(p)
            if len(tgt_idx) > 0:
                lens = gene_prot_len[tgt_idx]
                lens = lens[np.isfinite(lens)]
                if lens.size > 0:
                    mean_len = float(lens.mean())
                    scale = np.log1p(max(mean_len, 0.0))
                else:
                    scale = 0.0
            else:
                scale = 0.0

            out[i, :, 0] = add_resp * scale

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
