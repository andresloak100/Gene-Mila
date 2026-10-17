import numpy as np
from genemila.features.api import Feature, register


@register
class ProteinCompartmentSimilarityE169(Feature):
    name = "protein_compartment_similarity_e169"
    version = 1
    description = (
        "For each (p,g), Jaccard similarity between the set of protein compartment "
        "flags of the perturbation target(s) and gene g."
    )
    rationale = (
        "Genes whose proteins localize to the same compartment as the target protein "
        "may show correlated expression changes due to functional coupling."
    )
    inputs = ["protein_annotation", "target_indices"]
    params = {
        "compartments": [
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
    }
    dim = 1

    def compute(self, ctx, perts, params):
        comps = list(params.get("compartments", self.params["compartments"]))
        n_genes = ctx.n_genes
        n_perts = len(perts)

        # Build (n_genes, n_comps) boolean flag matrix from protein_annotation.
        flag_cache = ctx.cache.get("_pc_sim_e169_flags")
        if flag_cache is None:
            ann = ctx.knowledge("protein_annotation")
            genes_table = ann.get("genes", {}) if isinstance(ann, dict) else {}
            columns = ann.get("columns", []) if isinstance(ann, dict) else []
            col_idx = {c: i for i, c in enumerate(columns)}
            comp_cols = [col_idx.get(c, -1) for c in comps]
            flags = np.zeros((n_genes, len(comps)), dtype=bool)
            for gi, gene in enumerate(ctx.genes):
                vals = genes_table.get(gene)
                if vals is None:
                    continue
                row = np.zeros(len(comps), dtype=bool)
                for ci, cj in enumerate(comp_cols):
                    if cj < 0 or cj >= len(vals):
                        continue
                    v = vals[cj]
                    if v is None:
                        continue
                    try:
                        row[ci] = bool(float(v) > 0.5)
                    except (TypeError, ValueError):
                        row[ci] = False
                flags[gi] = row
            ctx.cache["_pc_sim_e169_flags"] = flags
            flag_cache = flags

        flags = flag_cache  # (n_genes, n_comps) bool
        gene_counts = flags.sum(axis=1).astype(np.float64)  # |G_g|

        out = np.zeros((n_perts, n_genes, 1), dtype=np.float64)

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            # Union of compartment flags over all target genes.
            tgt_flags = flags[tgt_idx].any(axis=0)  # (n_comps,)
            tgt_count = float(tgt_flags.sum())
            if tgt_count == 0:
                continue
            # Intersection counts: number of shared compartments per gene.
            inter = flags[:, tgt_flags].sum(axis=1).astype(np.float64)
            union = tgt_count + gene_counts - inter
            with np.errstate(divide="ignore", invalid="ignore"):
                jac = np.where(union > 0, inter / union, 0.0)
            out[i, :, 0] = jac

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
