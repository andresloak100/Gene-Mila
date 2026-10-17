import numpy as np
from genemila.features.api import Feature, register

_LOC_COLS = ["secreted", "membrane", "endoplasmic_reticulum", "golgi",
             "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome"]


@register
class TargetLocalizationSimilarity(Feature):
    name = "target_localization_similarity_e263"
    version = 1
    description = "Jaccard similarity between target gene(s) localization flags and gene g."
    rationale = ("Proteins in the same compartment are more likely to be functionally "
                 "linked, so perturbing a target may affect genes sharing localization.")
    inputs = ["protein_annotation"]
    params = {"default": "jaccard"}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        ann = ctx.knowledge("protein_annotation")
        if not ann or "genes" not in ann:
            return out

        cols = ann.get("columns", [])
        col_idx = {c: i for i, c in enumerate(cols)}
        if not all(c in col_idx for c in _LOC_COLS):
            return out

        gene_rows = ann["genes"]

        # Build boolean localization matrix (n_genes, n_flags)
        loc = np.zeros((n_genes, len(_LOC_COLS)), dtype=bool)
        for gi, g in enumerate(ctx.genes):
            vals = gene_rows.get(g)
            if not vals:
                continue
            for j, c in enumerate(_LOC_COLS):
                v = vals[col_idx[c]]
                if v is not None and v == v:  # not NaN
                    try:
                        if float(v) > 0:
                            loc[gi, j] = True
                    except (TypeError, ValueError):
                        pass

        n_flags = loc.sum(axis=1)  # per gene

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            t_idx = [ctx.gene_index[g] for g in tgenes if g in ctx.gene_index]
            if not t_idx:
                continue
            # Union of target localizations
            t_set = loc[t_idx].any(axis=0)
            t_count = int(t_set.sum())
            if t_count == 0:
                continue
            # Intersection with each gene
            inter = (loc & t_set).sum(axis=1).astype(float)
            union = n_flags + t_count - inter
            with np.errstate(divide="ignore", invalid="ignore"):
                jac = np.where(union > 0, inter / union, 0.0)
            out[i, :, 0] = jac

        out[~np.isfinite(out)] = 0.0
        return out
