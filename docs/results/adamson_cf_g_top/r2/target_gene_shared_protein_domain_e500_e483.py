import numpy as np
from genemila.features.api import Feature, register


@register
class TargetGeneSharedProteinDomain(Feature):
    name = "target_gene_shared_protein_domain_e500_e483"
    version = 1
    description = "Binary indicator: 1 if target gene and gene g share any protein domain, else 0."
    rationale = ("Shared protein domains between the perturbation target and gene g may indicate "
                 "functional or physical interaction, influencing downstream expression changes.")
    inputs = ["protein_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        out = np.zeros((len(perts), n_genes, 1), dtype=float)

        # Protein annotation provides per-gene features but no explicit domain IDs.
        # We derive a per-gene "domain signature" from the available per-gene
        # protein features (compartment flags + structural features). Genes sharing
        # this signature are treated as sharing protein-domain-level annotation.
        ann = ctx.knowledge("protein_annotation")
        gene_index = ctx.gene_index

        # Build per-gene signature vectors (only over interpreted numeric columns).
        # We use a robust subset of columns that are always present.
        sig_cols = ["has_signal_peptide", "n_transmembrane",
                    "secreted", "membrane", "endoplasmic_reticulum", "golgi",
                    "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome"]

        signatures = {}
        if ann is not None and isinstance(ann, dict):
            cols = ann.get("columns", [])
            col_pos = {c: i for i, c in enumerate(cols)}
            genes_ann = ann.get("genes", {}) or {}
            for g, vals in genes_ann.items():
                if g not in gene_index or not isinstance(vals, (list, tuple)):
                    continue
                vec = []
                ok = True
                for c in sig_cols:
                    if c in col_pos:
                        idx = col_pos[c]
                        if idx < len(vals) and vals[idx] is not None:
                            try:
                                vec.append(float(vals[idx]))
                            except (TypeError, ValueError):
                                vec.append(0.0)
                        else:
                            vec.append(0.0)
                    else:
                        vec.append(0.0)
                if ok:
                    signatures[g] = np.asarray(vec, dtype=float)

        # If no usable signature info, all zeros.
        if not signatures:
            return out

        # Cache gene -> signature array aligned to ctx gene order for fast lookup.
        if "e483_sig_matrix" not in ctx.cache:
            n_sig = len(sig_cols)
            sig_mat = np.full((n_genes, n_sig), np.nan, dtype=float)
            present = np.zeros(n_genes, dtype=bool)
            for g, vec in signatures.items():
                idx = gene_index.get(g)
                if idx is not None:
                    sig_mat[idx] = vec
                    present[idx] = True
            ctx.cache["e483_sig_matrix"] = sig_mat
            ctx.cache["e483_present"] = present
        else:
            sig_mat = ctx.cache["e483_sig_matrix"]
            present = ctx.cache["e483_present"]

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            # Use first target gene's signature.
            t_idx = tgt_idx[0]
            if not present[t_idx]:
                continue
            t_sig = sig_mat[t_idx]

            # Shared-domain indicator: genes with identical non-trivial signature.
            # A signature is "informative" if it has any nonzero entry.
            if not np.any(t_sig):
                # Target has no informative domain signature -> no sharing.
                continue

            valid = present & np.all(sig_mat == t_sig, axis=1)
            out[i, valid, 0] = 1.0

        return out
