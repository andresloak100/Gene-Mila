import numpy as np
from genemila.features.api import Feature, register

_COMPARTMENTS = [
    "secreted", "membrane", "endoplasmic_reticulum", "golgi",
    "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome",
]


@register
class TargetGeneCompartmentSimilarity(Feature):
    name = "target_gene_compartment_similarity_e370"
    version = 1
    description = (
        "Cosine/Jaccard similarity between the binary compartment-localization "
        "vectors (from protein_annotation) of the perturbation target and gene g."
    )
    rationale = (
        "Perturbing a target localized to a compartment may affect genes whose "
        "products localize to the same compartment; a colocalization score over "
        "all compartments captures this broadly."
    )
    inputs = ["protein_annotation"]
    params = {"similarity": "cosine"}
    dim = 1

    def _build_vectors(self, ctx, params):
        key = ("compartment_vectors", params.get("similarity", "cosine"))
        cache = ctx.cache
        if key in cache:
            return cache[key]

        n = ctx.n_genes
        vecs = np.zeros((n, len(_COMPARTMENTS)), dtype=np.float64)

        ann = ctx.knowledge("protein_annotation")
        genes_table = None
        cols = None
        if isinstance(ann, dict):
            genes_table = ann.get("genes")
            cols = ann.get("columns")
        if genes_table is None:
            cols = _COMPARTMENTS
            genes_table = {}

        # Map compartment -> column index in the protein_annotation value vector
        col_idx = {}
        if cols is not None:
            for c in _COMPARTMENTS:
                if c in cols:
                    col_idx[c] = cols.index(c)
        # Fallback: assume the last 9 columns are the compartment flags
        if not col_idx:
            base = None
            for c in _COMPARTMENTS:
                col_idx[c] = None  # resolved per-gene below

        for gi, g in enumerate(ctx.genes):
            vals = genes_table.get(g) if isinstance(genes_table, dict) else None
            if not vals:
                continue
            try:
                arr = np.asarray(vals, dtype=np.float64)
            except (TypeError, ValueError):
                continue
            for ci, c in enumerate(_COMPARTMENTS):
                idx = col_idx.get(c)
                if idx is None:
                    # fallback: last 9 entries are the compartment flags
                    if arr.size >= len(_COMPARTMENTS):
                        idx = arr.size - len(_COMPARTMENTS) + ci
                    else:
                        continue
                if idx < arr.size:
                    v = arr[idx]
                    if np.isfinite(v) and v > 0.5:
                        vecs[gi, ci] = 1.0

        # Precompute norms for cosine
        norms = np.linalg.norm(vecs, axis=1)
        cache[key] = (vecs, norms)
        return cache[key]

    def compute(self, ctx, perts, params):
        vecs, norms = self._build_vectors(ctx, params)
        mode = params.get("similarity", "cosine")
        n = ctx.n_genes
        out = np.zeros((len(perts), n, 1), dtype=np.float64)

        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if not t_idx:
                continue
            t_vec = vecs[t_idx].sum(axis=0)
            t_norm = np.linalg.norm(t_vec)
            if t_norm == 0.0:
                continue

            if mode == "jaccard":
                t_bin = (t_vec > 0.5).astype(np.float64)
                inter = vecs @ t_bin
                g_bin = (vecs > 0.5).astype(np.float64)
                union = g_bin.sum(axis=1) + t_bin.sum() - inter
                sim = np.where(union > 0, inter / np.maximum(union, 1e-12), 0.0)
            else:
                # cosine
                denom = norms * t_norm
                dots = vecs @ t_vec
                sim = np.where(denom > 0, dots / np.maximum(denom, 1e-12), 0.0)

            out[i, :, 0] = np.nan_to_num(sim, nan=0.0, posinf=0.0, neginf=0.0)

        return out
