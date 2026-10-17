import numpy as np
from genemila.features.api import Feature, register

@register
class TargetLengthXGeneMembranePropensity(Feature):
    name = "target_length_x_gene_membrane_propensity_e420"
    version = 1
    description = ("Product of the perturbation target's protein length and the continuous "
                   "membrane propensity of gene g (number of transmembrane domains).")
    rationale = ("Long proteins often participate in large membrane-associated complexes; "
                 "a continuous transmembrane count better captures membrane propensity than a "
                 "binary flag, so target protein length times gene transmembrane count should "
                 "predict membrane-gene sensitivity to complex stoichiometry disruption.")
    inputs = ["protein_annotation"]
    params = {}
    dim = 1

    def compute(self, ctx, perts, params):
        n_genes = ctx.n_genes
        prot = ctx.knowledge("protein_annotation")

        # Default membrane propensity (n_transmembrane) per gene.
        tm = np.zeros(n_genes, dtype=float)
        prot_len = np.zeros(n_genes, dtype=float)

        if prot is not None:
            genes_map = prot.get("genes", {}) or {}
            cols = prot.get("columns", []) or []
            # Locate column indices robustly.
            try:
                idx_tm = cols.index("n_transmembrane")
            except ValueError:
                idx_tm = None
            try:
                idx_len = cols.index("protein_length")
            except ValueError:
                idx_len = None

            gene_index = ctx.gene_index
            for sym, vals in genes_map.items():
                gi = gene_index.get(sym)
                if gi is None or vals is None:
                    continue
                if idx_tm is not None and idx_tm < len(vals):
                    v = vals[idx_tm]
                    if v is not None:
                        try:
                            tm[gi] = float(v)
                        except (TypeError, ValueError):
                            pass
                if idx_len is not None and idx_len < len(vals):
                    v = vals[idx_len]
                    if v is not None:
                        try:
                            prot_len[gi] = float(v)
                        except (TypeError, ValueError):
                            pass

        # Sanitize.
        tm = np.nan_to_num(tm, nan=0.0, posinf=0.0, neginf=0.0)
        prot_len = np.nan_to_num(prot_len, nan=0.0, posinf=0.0, neginf=0.0)

        out = np.zeros((len(perts), n_genes, 1), dtype=float)
        for i, p in enumerate(perts):
            tgt = ctx.target_indices(p)
            if not tgt:
                continue
            # Target protein length: use mean if multiple target columns.
            tlen = float(np.mean(prot_len[tgt]))
            out[i, :, 0] = tlen * tm

        out = np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)
        return out
