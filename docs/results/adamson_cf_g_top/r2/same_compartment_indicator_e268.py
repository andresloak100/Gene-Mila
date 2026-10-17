import numpy as np
from genemila.features.api import Feature, register

@register
class SameCompartmentIndicatorE268(Feature):
    name = "same_compartment_indicator_e268"
    version = 1
    description = "1 if target gene and gene g share at least one UniProt subcellular localization flag."
    rationale = "Perturbation of a compartment-localized target may affect genes whose products localize to the same compartment."
    inputs = ["protein_annotation"]
    params = {}
    dim = 1

    COMPARTMENT_COLUMNS = [
        "secreted", "membrane", "endoplasmic_reticulum", "golgi",
        "mitochondrion", "nucleus", "cytoplasm", "lysosome", "peroxisome",
    ]

    def _get_flags(self, ctx):
        cached = ctx.cache.get("e268_flags")
        if cached is not None:
            return cached

        pa = ctx.knowledge("protein_annotation")
        n_genes = ctx.n_genes
        flags = np.zeros((n_genes, len(self.COMPARTMENT_COLUMNS)), dtype=np.float32)

        if pa is not None and isinstance(pa, dict):
            columns = pa.get("columns", [])
            genes_table = pa.get("genes", {}) or {}
            col_idx = {}
            for c in self.COMPARTMENT_COLUMNS:
                if c in columns:
                    col_idx[c] = columns.index(c)
            if col_idx:
                for gene, values in genes_table.items():
                    gi = ctx.gene_index.get(gene)
                    if gi is None or values is None:
                        continue
                    for c, ci in col_idx.items():
                        try:
                            v = values[ci]
                        except (IndexError, TypeError):
                            continue
                        if v is None:
                            continue
                        try:
                            fv = float(v)
                        except (TypeError, ValueError):
                            continue
                        if np.isfinite(fv) and fv > 0:
                            flags[gi, self.COMPARTMENT_COLUMNS.index(c)] = 1.0

        ctx.cache["e268_flags"] = flags
        return flags

    def compute(self, ctx, perts, params):
        flags = self._get_flags(ctx)
        out = np.zeros((len(perts), ctx.n_genes, 1), dtype=np.float32)

        for i, p in enumerate(perts):
            tgt_idx = ctx.target_indices(p)
            if not tgt_idx:
                continue
            tgt_flags = flags[tgt_idx].max(axis=0)  # union over targets
            if tgt_flags.sum() == 0:
                continue
            overlap = flags @ tgt_flags  # (n_genes,)
            out[i, :, 0] = (overlap > 0).astype(np.float32)

        out[~np.isfinite(out)] = 0.0
        return out
