import numpy as np
from genemila.features.api import Feature, register


@register
class TargetLocalizationSimilarity(Feature):
    name = "target_localization_similarity_e520"
    version = 1
    description = "Similarity between gene g's subcellular localization flags and perturbation target gene's flags."
    rationale = "Perturbation effects depend on subcellular localization; genes sharing compartments with the target are more affected."
    inputs = ["protein_annotation", "target_genes"]
    params = {"similarity": "cosine"}
    dim = 1

    # localization flag columns from protein_annotation
    LOC_COLS = [
        "secreted", "membrane", "endoplasmic_reticulum", "golgi",
        "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome",
    ]

    def _build_matrix(self, ctx):
        ann = ctx.knowledge("protein_annotation")
        n = ctx.n_genes
        nloc = len(self.LOC_COLS)
        mat = np.zeros((n, nloc), dtype=float)
        if ann is None:
            return mat
        cols = ann.get("columns", [])
        genes = ann.get("genes", {})
        col_pos = {}
        for j, c in enumerate(self.LOC_COLS):
            if c in cols:
                col_pos[j] = cols.index(c)
        for g, gi in ctx.gene_index.items():
            vals = genes.get(g)
            if vals is None:
                continue
            for j, cp in col_pos.items():
                v = vals[cp]
                if v is not None:
                    try:
                        mat[gi, j] = float(v)
                    except (TypeError, ValueError):
                        mat[gi, j] = 0.0
        return mat

    def compute(self, ctx, perts, params):
        sim_mode = params.get("similarity", "cosine")
        loc = self._build_matrix(ctx)
        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1), dtype=float)

        # precompute norms
        if sim_mode == "cosine":
            norms = np.linalg.norm(loc, axis=1)
            denom_g = norms.copy()
            denom_g[denom_g == 0] = 1.0
        else:
            denom_g = None

        for i, p in enumerate(perts):
            tgenes = ctx.target_genes(p)
            tidx = [ctx.gene_index[g] for g in tgenes if g in ctx.gene_index]
            if not tidx:
                continue
            tvec = loc[tidx].mean(axis=0)  # (nloc,)
            if sim_mode == "cosine":
                tnorm = np.linalg.norm(tvec)
                if tnorm == 0:
                    continue
                dots = loc @ tvec  # (n,)
                sim = dots / (denom_g * tnorm)
                sim = np.clip(sim, -1.0, 1.0)
                out[i, :, 0] = sim
            else:  # jaccard on binarized flags
                tbin = (tvec > 0).astype(float)
                gbin = (loc > 0).astype(float)
                inter = gbin @ tbin
                union = gbin.sum(axis=1) + tbin.sum() - inter
                union[union == 0] = 1.0
                out[i, :, 0] = inter / union

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
