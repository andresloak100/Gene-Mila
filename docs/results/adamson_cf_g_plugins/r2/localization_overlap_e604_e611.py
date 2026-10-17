import numpy as np
from genemila.features.api import Feature, register


@register
class LocalizationOverlap(Feature):
    name = "localization_overlap_e604_e611"
    version = 1
    description = "Jaccard similarity between subcellular localization flag sets of target and gene."
    rationale = ("Proteins in the same compartment may be functionally related and respond "
                 "similarly to perturbations.")
    inputs = ["protein_annotation", "target_indices"]
    params = {}
    dim = 1

    # compartment flag columns in protein_annotation
    COMPARTMENTS = [
        "secreted", "membrane", "endoplasmic_reticulum", "golgi",
        "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome",
    ]

    def _build_flag_matrix(self, ctx):
        cached = ctx.cache.get("loc_overlap_flags")
        if cached is not None:
            return cached
        n = ctx.n_genes
        flags = np.zeros((n, len(self.COMPARTMENTS)), dtype=np.float64)
        ann = ctx.knowledge("protein_annotation")
        if ann is not None:
            genes = ann.get("genes", {})
            cols = ann.get("columns", [])
            col_idx = {c: i for i, c in enumerate(cols)}
            present = [col_idx[c] for c in self.COMPARTMENTS if c in col_idx]
            comp_positions = [self.COMPARTMENTS.index(c) for c in self.COMPARTMENTS if c in col_idx]
            for g, name in enumerate(ctx.genes):
                vals = genes.get(name)
                if vals is None:
                    continue
                for pos, ci in zip(comp_positions, present):
                    v = vals[ci]
                    if v is not None:
                        try:
                            if float(v) > 0:
                                flags[g, pos] = 1.0
                        except (TypeError, ValueError):
                            pass
        # number of set bits per gene
        counts = flags.sum(axis=1)
        ctx.cache["loc_overlap_flags"] = (flags, counts)
        return flags, counts

    def compute(self, ctx, perts, params):
        flags, counts = self._build_flag_matrix(ctx)
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=np.float64)
        for i, p in enumerate(perts):
            tidx = ctx.target_indices(p)
            if not tidx:
                continue
            t = tidx[0]
            t_flags = flags[t]
            t_count = counts[t]
            inter = flags @ t_flags  # (n_genes,)
            union = counts + t_count - inter
            with np.errstate(divide="ignore", invalid="ignore"):
                sim = np.where(union > 0, inter / union, 0.0)
            out[i, :, 0] = sim
        return out
