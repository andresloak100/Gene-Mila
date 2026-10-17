import numpy as np
from genemila.features.api import Feature, register


@register
class TargetProteinLengthE619(Feature):
    name = "target_protein_length_e619"
    version = 1
    description = "Protein length of the perturbation target gene, broadcast to all genes."
    rationale = (
        "Longer proteins may have more interaction domains or be more sensitive to "
        "knockdown, affecting downstream expression changes."
    )
    inputs = ["protein_annotation", "targets"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_perts = len(perts)
        n_genes = ctx.n_genes

        # Load protein annotation
        prot = ctx.knowledge("protein_annotation")
        prot_genes = {}
        if prot is not None and isinstance(prot, dict):
            prot_genes = prot.get("genes", {}) or {}

        # Determine column index for protein_length
        length_idx = 0
        if prot is not None and isinstance(prot, dict):
            cols = prot.get("columns", None)
            if cols is not None:
                try:
                    length_idx = list(cols).index("protein_length")
                except (ValueError, TypeError):
                    length_idx = 0

        # Build per-gene protein length lookup, defaulting to median
        gene_len = np.full(n_genes, np.nan, dtype=np.float64)
        for gi, g in enumerate(ctx.genes):
            rec = prot_genes.get(g, None)
            if rec is None:
                continue
            try:
                val = rec[length_idx]
            except (IndexError, TypeError):
                continue
            if val is None:
                continue
            try:
                fval = float(val)
            except (TypeError, ValueError):
                continue
            if np.isfinite(fval):
                gene_len[gi] = fval

        finite_mask = np.isfinite(gene_len)
        if finite_mask.any():
            median_val = float(np.median(gene_len[finite_mask]))
        else:
            median_val = 0.0

        gene_len = np.where(finite_mask, gene_len, median_val)

        # Cache target protein lengths per perturbation
        cache = ctx.cache
        cache_key = "_e619_target_prot_len"
        if cache_key not in cache:
            cache[cache_key] = {}

        target_len_cache = cache[cache_key]

        out = np.empty((n_perts, n_genes, 1), dtype=np.float64)
        for i, p in enumerate(perts):
            if p in target_len_cache:
                tlen = target_len_cache[p]
            else:
                tgenes = ctx.target_genes(p)
                vals = []
                for tg in tgenes:
                    gi = ctx.gene_index.get(tg, None)
                    if gi is not None and np.isfinite(gene_len[gi]):
                        vals.append(gene_len[gi])
                if vals:
                    tlen = float(np.mean(vals))
                else:
                    tlen = median_val
                target_len_cache[p] = tlen
            out[i, :, 0] = tlen

        return out
