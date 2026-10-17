import numpy as np
from genemila.features.api import Feature, register


@register
class TargetNTranscriptsTimesAdditiveE484(Feature):
    name = "target_n_transcripts_times_additive_e484"
    version = 1
    description = "Mean n_transcripts of p's target genes, multiplied by additive_response."
    rationale = ("Genes with many transcripts may have complex regulation, altering "
                 "activation outcomes, so isoform diversity of targets modulates the "
                 "additive response.")
    inputs = ["control_cells", "gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        # Load n_transcripts per gene from gene_annotation knowledge.
        n_trans = np.full(n_genes, np.nan, dtype=float)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            cols = ann.get("columns", [])
            genes_tbl = ann.get("genes", {})
            if "n_transcripts" in cols:
                idx = cols.index("n_transcripts")
                for g, gi in ctx.gene_index.items():
                    vals = genes_tbl.get(g)
                    if vals is not None and len(vals) > idx:
                        v = vals[idx]
                        if v is not None:
                            try:
                                fv = float(v)
                                if np.isfinite(fv):
                                    n_trans[gi] = fv
                            except (TypeError, ValueError):
                                pass
        # Fallback for missing values: median of available, else 1.0
        finite_mask = np.isfinite(n_trans)
        if finite_mask.any():
            fill = float(np.median(n_trans[finite_mask]))
        else:
            fill = 1.0
        n_trans = np.where(finite_mask, n_trans, fill)

        # Additive response feature (composed).
        try:
            add = ctx.feature("additive_response", perts)
        except Exception:
            add = None

        for i, p in enumerate(perts):
            tgt = ctx.target_indices(p)
            if len(tgt) == 0:
                mean_nt = 0.0
            else:
                mean_nt = float(np.mean(n_trans[tgt]))

            if add is not None:
                add_vec = np.asarray(add[i], dtype=float).reshape(-1)
                if add_vec.shape[0] != n_genes:
                    # pad/truncate defensively
                    tmp = np.zeros(n_genes, dtype=float)
                    m = min(n_genes, add_vec.shape[0])
                    tmp[:m] = add_vec[:m]
                    add_vec = tmp
            else:
                add_vec = np.zeros(n_genes, dtype=float)

            out[i, :, 0] = mean_nt * add_vec

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
