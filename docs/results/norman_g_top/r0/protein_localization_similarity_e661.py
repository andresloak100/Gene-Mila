import numpy as np
from genemila.features.api import Feature, register


@register
class ProteinLocalizationSimilarityE661(Feature):
    name = "protein_localization_similarity_e661"
    version = 1
    description = "Jaccard similarity of compartment flag sets between gene g and perturbation targets."
    rationale = "Perturbations may propagate through proteins sharing subcellular compartments; shared localization indicates functional proximity."
    inputs = ["protein_annotation"]
    params = {"compartments": "secreted,membrane,endoplasmic_reticulum,golgi,mitochondrion,nucleus,cytoplasm,lysosome,peroxisome"}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        comp_names = [c.strip() for c in str(params.get("compartments", "")).split(",") if c.strip()]

        ann = ctx.knowledge("protein_annotation")
        gene_flag = np.zeros((n_genes, len(comp_names)), dtype=np.float32)

        if ann is not None and comp_names:
            genes_tbl = ann.get("genes", {}) or {}
            columns = ann.get("columns", []) or []
            col_index = {c: i for i, c in enumerate(columns)}
            # Map compartment name -> column index in annotation table
            comp_cols = []
            for c in comp_names:
                if c in col_index:
                    comp_cols.append(col_index[c])
                else:
                    comp_cols.append(-1)

            # Build gene -> row lookup
            for gi, gname in enumerate(ctx.genes):
                vals = genes_tbl.get(gname)
                if vals is None:
                    continue
                for j, ci in enumerate(comp_cols):
                    if ci is None or ci < 0:
                        continue
                    try:
                        v = vals[ci]
                    except (IndexError, TypeError):
                        v = None
                    if v is None:
                        continue
                    try:
                        gene_flag[gi, j] = 1.0 if float(v) > 0.5 else 0.0
                    except (TypeError, ValueError):
                        gene_flag[gi, j] = 0.0

        # Precompute per-gene set sizes
        gene_sizes = gene_flag.sum(axis=1)  # (n_genes,)

        cache = ctx.cache
        if "e661_gene_flag" not in cache:
            cache["e661_gene_flag"] = gene_flag
            cache["e661_gene_sizes"] = gene_sizes

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            # Union of compartments over target genes
            tgt_flags = gene_flag[tgt_idx, :]  # (n_t, n_comp)
            union = (tgt_flags.max(axis=0) > 0.5).astype(np.float32)  # (n_comp,)
            union_size = float(union.sum())
            if union_size == 0.0:
                continue
            # Intersection size per gene = sum over comps where both set
            inter = gene_flag @ union  # (n_genes,)
            union_broadcast = gene_sizes + union_size - inter
            # Avoid division by zero
            denom = np.where(union_broadcast > 0, union_broadcast, 1.0)
            jac = np.where(union_broadcast > 0, inter / denom, 0.0)
            out[i, :, 0] = jac

        # Ensure finite
        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
