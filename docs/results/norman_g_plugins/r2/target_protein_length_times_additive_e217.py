import numpy as np
from genemila.features.api import Feature, register

@register
class TargetProteinLengthTimesAdditiveE217(Feature):
    name = "target_protein_length_times_additive_e217"
    version = 1
    description = "Product of mean target-gene protein length and additive_response."
    rationale = ("Longer proteins have more domains and interaction partners, so activating "
                 "targets with long proteins may yield stronger downstream effects; scaling the "
                 "additive baseline by target protein length captures this structural property.")
    inputs = ["protein_annotation", "additive_response"]
    params = {"normalize": "log"}
    dim = 1

    def compute(self, ctx, perts, params):
        normalize = params.get("normalize", "log")
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1))

        # additive_response feature (n_perts, n_genes, 1)
        add = ctx.feature("additive_response", perts)
        add = np.asarray(add, dtype=float).reshape(len(perts), n_genes)

        # protein_annotation lookup
        prot = ctx.knowledge("protein_annotation")
        plen_map = {}
        if prot is not None:
            genes_tbl = prot.get("genes", {})
            cols = prot.get("columns", [])
            try:
                idx = cols.index("protein_length")
            except ValueError:
                idx = 0
            for sym, vals in genes_tbl.items():
                try:
                    v = vals[idx]
                except (IndexError, TypeError):
                    v = None
                if v is not None:
                    plen_map[sym] = float(v)

        # global fallback: mean of available protein lengths
        if plen_map:
            global_mean = float(np.mean(list(plen_map.values())))
        else:
            global_mean = 0.0

        for i, p in enumerate(perts):
            tg = ctx.target_genes(p)
            if tg:
                vals = [plen_map[g] for g in tg if g in plen_map]
                mean_len = float(np.mean(vals)) if vals else 0.0
            else:
                mean_len = 0.0

            if normalize == "log":
                scale = np.log1p(mean_len)
            elif normalize == "sqrt":
                scale = np.sqrt(mean_len)
            elif normalize == "none" or normalize is None:
                scale = mean_len
            else:
                scale = np.log1p(mean_len)

            out[i, :, 0] = scale * add[i]

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
