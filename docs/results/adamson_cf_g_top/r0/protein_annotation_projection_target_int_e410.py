import numpy as np
from genemila.features.api import Feature, register


@register
class ProteinAnnotationProjectionTargetIntE410(Feature):
    name = "protein_annotation_projection_target_int_e410"
    version = 1
    description = (
        "Dot product between random projections of protein annotation vectors for "
        "perturbation target and gene, multiplied by (1 - LOEUF_target)."
    )
    rationale = (
        "Protein annotation (length, signal peptide, transmembrane segments, "
        "compartment flags) captures functional properties; a random projection "
        "captures high-order nonlinear combinations. Interacting the target's "
        "projection with each gene's projection, scaled by target essentiality "
        "(1 - LOEUF), may reveal nonlinear target-gene functional relationships."
    )
    inputs = ["knowledge", "target_indices"]
    params = {"projection_dim": 20, "seed": 410}
    dim = 1

    def _protein_matrix(self, ctx, params):
        key = ("prot_annot_matrix", params.get("projection_dim", 20), params.get("seed", 410))
        cache = ctx.cache
        if key in cache:
            return cache[key]

        n_genes = ctx.n_genes
        prot = ctx.knowledge("protein_annotation")
        # Feature columns we extract per gene
        feat_names = [
            "protein_length",
            "has_signal_peptide",
            "signal_peptide_length",
            "n_transmembrane",
            "secreted",
            "membrane",
            "endoplasmic_reticulum",
            "golgi",
            "mitochondrion",
            "nucleus",
            "cytoplasm",
            "lysosome",
            "peroxisome",
        ]
        raw = np.zeros((n_genes, len(feat_names)), dtype=np.float64)
        cols = None
        genes_map = None
        if isinstance(prot, dict):
            cols = prot.get("columns")
            genes_map = prot.get("genes")

        if cols is not None and genes_map is not None:
            col_index = {c: i for i, c in enumerate(cols)}
            for j, fn in enumerate(feat_names):
                if fn in col_index:
                    ci = col_index[fn]
                    for gi, g in enumerate(ctx.genes):
                        vals = genes_map.get(g)
                        if vals is None:
                            continue
                        v = vals[ci]
                        if v is None:
                            continue
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv):
                            raw[gi, j] = fv

        # Log-transform length-like features to tame scale
        for j, fn in enumerate(feat_names):
            if fn in ("protein_length", "signal_peptide_length"):
                raw[:, j] = np.log1p(np.maximum(raw[:, j], 0.0))

        # Standardise each column (robustly)
        mean = raw.mean(axis=0)
        std = raw.std(axis=0)
        std[std < 1e-8] = 1.0
        std_raw = (raw - mean) / std

        # Random projection
        d = int(params.get("projection_dim", 20))
        seed = int(params.get("seed", 410))
        rng = np.random.RandomState(seed)
        R = rng.randn(len(feat_names), d) / np.sqrt(len(feat_names))

        proj = std_raw @ R  # (n_genes, d)

        cache[key] = (proj, std_raw)
        return cache[key]

    def _loeuf(self, ctx):
        key = "prot_annot_loeuf_vec"
        cache = ctx.cache
        if key in cache:
            return cache[key]

        n_genes = ctx.n_genes
        loeuf = np.full(n_genes, np.nan, dtype=np.float64)
        gc = ctx.knowledge("gene_constraint")
        if isinstance(gc, dict):
            cols = gc.get("columns")
            genes_map = gc.get("genes")
            if cols is not None and genes_map is not None:
                if "oe_lof_upper" in cols:
                    ci = cols.index("oe_lof_upper")
                    for gi, g in enumerate(ctx.genes):
                        vals = genes_map.get(g)
                        if vals is None:
                            continue
                        v = vals[ci]
                        if v is None:
                            continue
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv):
                            loeuf[gi] = fv
        cache[key] = loeuf
        return loeuf

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=np.float64)

        proj, _ = self._protein_matrix(ctx, params)
        loeuf = self._loeuf(ctx)

        # Fill missing LOEUF with median of observed (fallback 0.5)
        obs = loeuf[np.isfinite(loeuf)]
        fill = float(np.median(obs)) if obs.size > 0 else 0.5
        loeuf_filled = np.where(np.isfinite(loeuf), loeuf, fill)
        # Clamp to [0,1] for essentiality term
        loeuf_clipped = np.clip(loeuf_filled, 0.0, 1.0)
        essentiality = 1.0 - loeuf_clipped  # (n_genes,)

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            # Average projection over target genes (usually one)
            tgt_proj = proj[tgt_idx, :].mean(axis=0)  # (d,)
            tgt_ess = float(essentiality[tgt_idx].mean())

            # Dot product of target projection with gene projections
            dots = proj @ tgt_proj  # (n_genes,)
            out[i, :, 0] = dots * tgt_ess

        # Ensure finite
        out[~np.isfinite(out)] = 0.0
        return out
