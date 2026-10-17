import numpy as np
from genemila.features.api import Feature, register


@register
class TFBindingOverlap(Feature):
    name = "tf_binding_overlap_e610_e604"
    version = 1
    description = ("For each (p,g), overlap of TF-binding-motif proxies between the "
                   "target gene promoter and gene g promoter, normalized by total motifs.")
    rationale = ("Genes whose promoters share regulatory motif content with the perturbed "
                 "target's promoter may respond more strongly due to shared regulatory logic.")
    inputs = ["gene_annotation", "transcription_factors", "control_mean"]
    params = {"promoter_window": 1000}
    dim = 1

    def _motif_vectors(self, ctx, params):
        """Build a per-gene binary motif-proxy vector from gene_annotation promoter features."""
        cache = ctx.cache
        key = ("tf_overlap_motifs", params.get("promoter_window", 1000))
        if key in cache:
            return cache[key]

        ann = ctx.knowledge("gene_annotation")
        n_genes = ctx.n_genes
        genes = ctx.genes

        # Fallback: derive pseudo-motif signature from available numeric annotation columns.
        # We build a compact descriptor per gene from promoter-related annotation features.
        n_feat = 8
        V = np.zeros((n_genes, n_feat), dtype=np.float64)

        if ann is not None and isinstance(ann, dict) and "genes" in ann:
            cols = ann.get("columns", [])
            col_idx = {c: i for i, c in enumerate(cols)}
            gene_map = ann["genes"]
            # promoter-related columns if present
            want = ["gc_promoter", "cpg_oe_promoter", "n_tss_within_100kb",
                    "nearest_tss_kb", "n_upstream_atg", "gc_cds", "n_transcripts",
                    "n_exons"]
            for gi, g in enumerate(genes):
                vals = gene_map.get(g)
                if vals is None:
                    continue
                for fi, cname in enumerate(want):
                    ci = col_idx.get(cname)
                    if ci is None or ci >= len(vals):
                        continue
                    v = vals[ci]
                    if v is None:
                        continue
                    try:
                        V[gi, fi] = float(v)
                    except (TypeError, ValueError):
                        pass

        # Standardize columns robustly
        mu = np.nanmean(V, axis=0)
        sd = np.nanstd(V, axis=0)
        sd[sd < 1e-8] = 1.0
        V = (V - mu) / sd
        V = np.nan_to_num(V, nan=0.0, posinf=0.0, neginf=0.0)

        # Binarize each descriptor into "motif present" using median split (per column),
        # producing a binary motif-proxy vector per gene.
        med = np.median(V, axis=0)
        B = (V > med).astype(np.float64)
        # Ensure at least one motif per gene (avoid all-zero rows)
        empty = B.sum(axis=1) == 0
        if np.any(empty):
            B[empty, 0] = 1.0

        cache[key] = B
        return B

    def compute(self, ctx, perts, params):
        n = len(perts)
        n_genes = ctx.n_genes
        out = np.zeros((n, n_genes, 1), dtype=np.float64)

        B = self._motif_vectors(ctx, params)  # (n_genes, n_motifs) binary
        total = float(B.shape[1])

        # Precompute per-gene motif count (sum of binary vector; constant-ish)
        # Overlap between two binary vectors = dot product.
        # For each perturbation, target gene's motif vector is B[t].
        # Overlap(p,g) = B[t] . B[g] / total

        for i, p in enumerate(perts):
            t_idx = ctx.target_indices(p)
            if not t_idx:
                # No measured target: zero row (finite)
                continue
            # Use first targeted gene (single-gene targets in this dataset)
            t = t_idx[0]
            tv = B[t]  # (n_motifs,)
            overlaps = B @ tv  # (n_genes,)
            out[i, :, 0] = overlaps / total

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
