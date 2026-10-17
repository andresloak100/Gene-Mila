import numpy as np
from genemila.features.api import Feature, register


@register
class TargetMeanProteinLength(Feature):
    name = "target_mean_protein_length_e444"
    version = 1
    description = "Mean protein length of the target genes of each perturbation, from protein_annotation."
    rationale = ("Longer proteins have more interaction domains, which may modulate the magnitude "
                 "of the expression response to a perturbation.")
    inputs = ["knowledge", "target_genes"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        out = np.zeros((len(perts), ctx.n_genes, 1))

        # Load protein_annotation knowledge
        pa = ctx.knowledge("protein_annotation")
        if not pa or "genes" not in pa or "columns" not in pa:
            return out

        cols = pa["columns"]
        try:
            li = cols.index("protein_length")
        except ValueError:
            return out

        genes_tbl = pa["genes"]

        def prot_len(gene):
            vals = genes_tbl.get(gene)
            if vals is None:
                return None
            v = vals[li]
            if v is None:
                return None
            try:
                f = float(v)
            except (TypeError, ValueError):
                return None
            if not np.isfinite(f):
                return None
            return f

        for i, p in enumerate(perts):
            targets = ctx.target_genes(p)
            if not targets:
                continue
            lengths = []
            for g in targets:
                L = prot_len(g)
                if L is not None:
                    lengths.append(L)
            if lengths:
                val = float(np.mean(lengths))
                out[i, :, 0] = val

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
