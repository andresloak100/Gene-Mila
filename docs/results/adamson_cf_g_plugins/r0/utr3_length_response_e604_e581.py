import numpy as np
from genemila.features.api import Feature, register


@register
class Utr3LengthResponse(Feature):
    name = "utr3_length_response_e604_e581"
    version = 1
    description = "Interaction between gene 3' UTR length and perturbation response (target self-delta or mean response)."
    rationale = ("Genes with longer 3' UTRs are subject to more post-transcriptional regulation; "
                 "their response to a perturbation may be buffered, so UTR length modulates the "
                 "magnitude of the response signal.")
    inputs = ["control_cells", "train_delta", "knowledge"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        n_genes = ctx.n_genes

        # --- 3' UTR length per gene from gene_annotation (column index 6) ---
        utr = np.full(n_genes, np.nan, dtype=float)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            cols = ann.get("columns", [])
            try:
                idx = cols.index("utr3_length")
            except ValueError:
                idx = 6
            genes_map = ann.get("genes", {})
            for g in ctx.genes:
                vals = genes_map.get(g)
                if vals is not None and len(vals) > idx:
                    v = vals[idx]
                    if v is not None:
                        try:
                            fv = float(v)
                            if np.isfinite(fv):
                                utr[ctx.gene_index[g]] = fv
                        except (TypeError, ValueError):
                            pass

        # standardize UTR length (nan -> 0 after z-score of finite entries)
        finite = np.isfinite(utr)
        if finite.any():
            mu = utr[finite].mean()
            sd = utr[finite].std()
            if sd <= 0 or not np.isfinite(sd):
                sd = 1.0
            utr_z = np.zeros(n_genes, dtype=float)
            utr_z[finite] = (utr[finite] - mu) / sd
        else:
            utr_z = np.zeros(n_genes, dtype=float)

        out = np.zeros((n_perts, n_genes, 1), dtype=float)

        for i, p in enumerate(perts):
            # target self-delta: delta of the perturbation's own target gene(s)
            target_idx = ctx.target_indices(p)

            self_delta = None
            try:
                _, d = ctx.train_delta(exclude=p)
                if d.shape[0] > 0 and len(target_idx) > 0:
                    self_delta = float(np.mean(d[:, target_idx]))
            except Exception:
                self_delta = None

            if self_delta is None or not np.isfinite(self_delta):
                # fall back to mean_response (mean over training deltas)
                try:
                    _, d = ctx.train_delta(exclude=p)
                    if d.shape[0] > 0:
                        mr = d.mean(axis=0)
                        # use mean of mean_response as scalar proxy
                        self_delta = float(np.mean(mr))
                    else:
                        self_delta = 0.0
                except Exception:
                    self_delta = 0.0
                if not np.isfinite(self_delta):
                    self_delta = 0.0

            out[i, :, 0] = utr_z * self_delta

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
