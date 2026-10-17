import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveResponseXTargetNuclearCytopE648(Feature):
    name = "additive_response_x_target_nuclear_cytop_e648"
    version = 1
    description = ("Product of additive_response and the mean (nuclear - cytoplasm) "
                   "protein-localization flag across the perturbation's target genes.")
    rationale = ("CRISPRa of nuclear proteins (e.g. transcription factors) may drive "
                 "direct transcriptional programs, while cytoplasmic/membrane targets act "
                 "more indirectly; the nuclear-cytoplasmic bias of targets should modulate "
                 "the additive response.")
    inputs = ["protein_annotation", "additive_response"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes

        # additive_response feature (n_perts, n_genes, 1)
        add = ctx.feature("additive_response", perts, params=None)
        add = np.asarray(add, dtype=float)
        if add.ndim == 3:
            add = add[:, :, 0]
        elif add.ndim == 1:
            add = add[:, None]

        # Parse protein_annotation for nuclear / cytoplasm flags
        ann = ctx.knowledge("protein_annotation")
        nuc_flag = np.zeros(n_genes, dtype=float)
        cyt_flag = np.zeros(n_genes, dtype=float)

        if ann is not None:
            cols = ann.get("columns", [])
            genes_tbl = ann.get("genes", {}) or {}
            try:
                i_nuc = cols.index("nucleus")
            except ValueError:
                i_nuc = None
            try:
                i_cyt = cols.index("cytoplasm")
            except ValueError:
                i_cyt = None

            for g, vals in genes_tbl.items():
                gi = ctx.gene_index.get(g)
                if gi is None or vals is None:
                    continue
                if i_nuc is not None and i_nuc < len(vals) and vals[i_nuc] is not None:
                    try:
                        nuc_flag[gi] = float(vals[i_nuc])
                    except (TypeError, ValueError):
                        pass
                if i_cyt is not None and i_cyt < len(vals) and vals[i_cyt] is not None:
                    try:
                        cyt_flag[gi] = float(vals[i_cyt])
                    except (TypeError, ValueError):
                        pass

        nuc_minus_cyt = nuc_flag - cyt_flag  # (n_genes,)

        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            tgt = ctx.target_indices(p)
            if len(tgt) == 0:
                bias = 0.0
            else:
                bias = float(nuc_minus_cyt[np.asarray(tgt, dtype=int)].mean())
            out[i, :, 0] = add[i] * bias

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
