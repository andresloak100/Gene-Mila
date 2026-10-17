import numpy as np
from genemila.features.api import Feature, register

@register
class AdditiveResponseXTargetNuclear(Feature):
    name = "additive_response_x_target_nuclear_e542"
    version = 1
    description = "Product of additive_response and the mean nuclear-protein flag of the perturbation's target genes."
    rationale = ("CRISPRa perturbs target expression; nuclear-localized target proteins may have more "
                 "direct transcriptional effects than membrane/cytoplasmic ones, so the additive response "
                 "may be modulated by target subcellular localization.")
    inputs = ["control_cells", "protein_annotation", "additive_response"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        n_perts = len(perts)

        # additive_response feature: (n_perts, n_genes, 1)
        add = ctx.feature("additive_response", perts)
        if add.ndim == 3:
            add = add[:, :, 0]
        add = np.asarray(add, dtype=float)

        # Load protein annotation nuclear flag
        pa = ctx.knowledge("protein_annotation")
        nuclear_flag = np.zeros(n_genes, dtype=float)
        if pa is not None and "genes" in pa and "columns" in pa:
            cols = pa["columns"]
            try:
                idx = cols.index("nucleus")
            except ValueError:
                idx = None
            if idx is not None:
                genes_dict = pa["genes"]
                for g, col in ctx.gene_index.items():
                    vals = genes_dict.get(g)
                    if vals is None:
                        continue
                    v = vals[idx]
                    if v is None:
                        continue
                    try:
                        nuclear_flag[col] = 1.0 if float(v) > 0 else 0.0
                    except (TypeError, ValueError):
                        nuclear_flag[col] = 0.0

        out = np.zeros((n_perts, n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if tgt_idx:
                nuc = float(np.mean(nuclear_flag[tgt_idx]))
            else:
                nuc = 0.0
            out[i, :, 0] = add[i] * nuc

        out[~np.isfinite(out)] = 0.0
        return out
