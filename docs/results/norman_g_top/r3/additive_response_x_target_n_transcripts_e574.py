import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveResponseXTargetNTranscripts(Feature):
    name = "additive_response_x_target_n_transcripts_e574"
    version = 1
    description = "Product of additive_response and the mean number of transcripts of the perturbation's target genes."
    rationale = "Gene complexity (n_transcripts) may modulate how CRISPRa activation of target genes translates into expression changes."
    inputs = ["gene_annotation", "train_delta"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=float)

        ann = ctx.knowledge("gene_annotation")
        columns = ann.get("columns", []) if ann else []
        genes_tbl = ann.get("genes", {}) if ann else {}
        try:
            n_tr_idx = columns.index("n_transcripts")
        except ValueError:
            n_tr_idx = None

        # Precompute additive response per perturbation using training deltas.
        for i, p in enumerate(perts):
            # additive baseline: sum over target genes of each gene's mean delta
            _, d = ctx.train_delta(exclude=p)
            mean_delta = d.mean(axis=0)  # (n_genes,)
            tgt_idx = ctx.target_indices(p)
            if tgt_idx:
                add_resp = mean_delta[tgt_idx].sum()
            else:
                add_resp = 0.0

            # mean n_transcripts over target genes
            tgt_genes = ctx.target_genes(p)
            vals = []
            if n_tr_idx is not None:
                for g in tgt_genes:
                    row = genes_tbl.get(g)
                    if row is None:
                        continue
                    try:
                        v = row[n_tr_idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        vals.append(fv)
            mean_ntr = float(np.mean(vals)) if vals else 0.0

            out[i, :, 0] = add_resp * mean_ntr

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
