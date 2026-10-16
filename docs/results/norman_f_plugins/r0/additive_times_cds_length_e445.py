import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveTimesCdsLengthE445(Feature):
    name = "additive_times_cds_length_e445"
    version = 1
    description = "Elementwise product of additive_response and cds_length of gene g."
    rationale = "Longer CDS may require more transcriptional machinery, altering response magnitude."
    inputs = ["gene_annotation", "additive_response"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n = len(perts)
        out = np.zeros((n, ctx.n_genes, 1), dtype=float)

        # additive_response feature
        add = ctx.feature("additive_response", perts)
        add = np.asarray(add, dtype=float)
        if add.ndim == 3:
            add = add[:, :, 0]
        elif add.ndim == 1:
            add = add.reshape(1, -1)

        # CDS length per gene from gene_annotation prior knowledge
        ann = ctx.knowledge("gene_annotation")
        cds = np.zeros(ctx.n_genes, dtype=float)
        if ann is not None and "genes" in ann and ann["genes"]:
            genes_info = ann["genes"]
            cols = ann.get("columns", [])
            cds_idx = None
            for j, c in enumerate(cols):
                if c == "cds_length":
                    cds_idx = j
                    break
            if cds_idx is not None:
                for gi, g in enumerate(ctx.genes):
                    vals = genes_info.get(g)
                    if vals is None:
                        continue
                    v = vals[cds_idx]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv):
                        cds[gi] = fv

        out[:, :, 0] = add * cds[None, :]
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
