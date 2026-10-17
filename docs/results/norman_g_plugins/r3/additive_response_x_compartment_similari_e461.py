import numpy as np
from genemila.features.api import Feature, register


@register
class AdditiveResponseXCompartmentSimilarityE461(Feature):
    name = "additive_response_x_compartment_similari_e461"
    version = 1
    description = "Product of additive_response and cosine similarity between the perturbation's target protein compartment profile and gene g's compartment profile."
    rationale = "CRISPRa perturbations affect protein abundance; downstream effects may propagate through shared cellular compartments, so responses may be amplified when target and responding proteins localize to the same compartment."
    inputs = ["control_cells", "protein_annotation", "train_delta"]
    params = {}
    dim = 1

    COMPARTMENTS = [
        "secreted", "membrane", "endoplasmic_reticulum", "golgi",
        "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome",
    ]

    def _build_profiles(self, ctx):
        cache = ctx.cache
        key = "_e461_profiles"
        if key in cache:
            return cache[key]

        ann = ctx.knowledge("protein_annotation")
        n_genes = ctx.n_genes
        n_comp = len(self.COMPARTMENTS)
        profiles = np.zeros((n_genes, n_comp), dtype=np.float64)

        if ann is not None and isinstance(ann, dict):
            genes = ann.get("genes", {}) or {}
            cols = ann.get("columns", []) or []
            col_idx = {c: i for i, c in enumerate(cols)}
            comp_cols = [col_idx[c] for c in self.COMPARTMENTS if c in col_idx]

            for g, col in ctx.gene_index.items():
                vals = genes.get(g)
                if vals is None:
                    continue
                for j, c in enumerate(self.COMPARTMENTS):
                    ci = col_idx.get(c)
                    if ci is None:
                        continue
                    v = vals[ci]
                    if v is None:
                        continue
                    try:
                        fv = float(v)
                    except (TypeError, ValueError):
                        continue
                    if np.isfinite(fv) and fv > 0.5:
                        profiles[col, j] = 1.0

        # Precompute norms (0 for all-zero rows)
        norms = np.linalg.norm(profiles, axis=1)
        cache[key] = (profiles, norms)
        return profiles, norms

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        profiles, norms = self._build_profiles(ctx)
        out = np.zeros((len(perts), n_genes, 1), dtype=np.float64)

        for i, p in enumerate(perts):
            _, d = ctx.train_delta(exclude=p)
            add = d.mean(axis=0)  # (n_genes,)

            t_idx = ctx.target_indices(p)
            if len(t_idx) == 0:
                continue
            t_prof = profiles[t_idx].mean(axis=0)  # (n_comp,)
            t_norm = np.linalg.norm(t_prof)

            if t_norm <= 0:
                continue

            # cosine similarity between t_prof and each gene's profile
            dots = profiles @ t_prof  # (n_genes,)
            denom = norms * t_norm
            sim = np.zeros(n_genes, dtype=np.float64)
            nz = denom > 0
            sim[nz] = dots[nz] / denom[nz]

            out[i, :, 0] = add * sim

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
