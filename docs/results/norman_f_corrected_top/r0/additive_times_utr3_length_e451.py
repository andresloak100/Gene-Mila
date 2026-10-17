import numpy as np
from genemila.features.api import Feature, FeatureContext, register


@register
class AdditiveTimesUtr3LengthE451(Feature):
    name = "additive_times_utr3_length_e451"
    version = 1
    description = "Elementwise product of additive_response and utr3_length of gene g."
    rationale = (
        "3' UTR length influences mRNA stability and post-transcriptional regulation; "
        "interacting it with the additive response may capture gene-specific modulation."
    )
    inputs = ["gene_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx: FeatureContext, perts: list[str], params: dict) -> np.ndarray:
        n_perts = len(perts)
        n_genes = ctx.n_genes

        # additive_response feature: (n_perts, n_genes, 1)
        add = ctx.feature("additive_response", perts)
        add = np.asarray(add, dtype=float)
        if add.ndim == 3:
            add = add[:, :, 0]
        elif add.ndim == 2:
            pass
        else:
            add = add.reshape(n_perts, n_genes)

        # utr3_length per gene from gene_annotation
        utr3 = np.zeros(n_genes, dtype=float)
        ann = ctx.knowledge("gene_annotation")
        if ann is not None:
            genes_ann = ann.get("genes") if isinstance(ann, dict) else None
            if isinstance(genes_ann, dict):
                columns = ann.get("columns") if isinstance(ann, dict) else None
                idx = None
                if isinstance(columns, list):
                    for j, c in enumerate(columns):
                        if c == "utr3_length":
                            idx = j
                            break
                if idx is None:
                    idx = 6  # fallback per documented column order
                for gi, g in enumerate(ctx.genes):
                    vals = genes_ann.get(g)
                    if vals is None:
                        continue
                    try:
                        v = vals[idx]
                    except (IndexError, TypeError):
                        continue
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        utr3[gi] = fv

        out = np.zeros((n_perts, n_genes, 1), dtype=float)
        out[:, :, 0] = add * utr3[None, :]

        # ensure finite
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
