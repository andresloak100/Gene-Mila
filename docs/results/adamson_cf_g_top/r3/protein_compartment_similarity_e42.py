import numpy as np
from genemila.features.api import Feature, register


@register
class ProteinCompartmentSimilarityE42(Feature):
    name = "protein_compartment_similarity_e42"
    version = 1
    description = ("Jaccard similarity between the set of subcellular-compartment flags "
                   "(from protein_annotation) of gene g and of the perturbation target.")
    rationale = ("Proteins localizing to the same compartment as the perturbed target may be "
                 "co-regulated and show correlated expression changes.")
    inputs = ["protein_annotation", "target_genes"]
    params = {}
    dim = 1

    # compartment flag columns in protein_annotation
    COMPARTMENTS = [
        "secreted", "membrane", "endoplasmic_reticulum", "golgi",
        "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome",
    ]

    def _flag_matrix(self, ctx):
        cached = ctx.cache.get("pcs_e42_flags")
        if cached is not None:
            return cached

        n = ctx.n_genes
        flags = np.zeros((n, len(self.COMPARTMENTS)), dtype=bool)
        ann = ctx.knowledge("protein_annotation")
        if ann is not None:
            genes = ann.get("genes", {}) or {}
            cols = ann.get("columns", []) or []
            col_idx = {c: i for i, c in enumerate(cols)}
            idxs = [col_idx.get(c) for c in self.COMPARTMENTS]
            for g, gi in ctx.gene_index.items():
                vals = genes.get(g)
                if vals is None:
                    continue
                for j, ci in enumerate(idxs):
                    if ci is None or ci >= len(vals):
                        continue
                    v = vals[ci]
                    if v is None:
                        continue
                    try:
                        flags[gi, j] = float(v) > 0.5
                    except (TypeError, ValueError):
                        pass
        ctx.cache["pcs_e42_flags"] = flags
        return flags

    def compute(self, ctx, perts, params):
        flags = self._flag_matrix(ctx)
        counts = flags.sum(axis=1).astype(np.float64)
        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1), dtype=np.float64)

        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if not t_idx:
                continue
            # union flag set over target genes (typically one)
            t_vec = flags[t_idx].any(axis=0).astype(np.float64)
            t_count = float(t_vec.sum())
            if t_count == 0.0:
                continue
            inter = flags.astype(np.float64) @ t_vec
            union = counts + t_count - inter
            sim = np.zeros(n, dtype=np.float64)
            nz = union > 0
            sim[nz] = inter[nz] / union[nz]
            out[i, :, 0] = sim

        return out
